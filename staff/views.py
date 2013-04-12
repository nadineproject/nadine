import traceback
import time as timeo
from datetime import date, datetime, timedelta
import calendar
from decimal import Decimal
from collections import namedtuple

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

import settings
from models import *
from forms import *
import billing, user_reports, email

START_DATE_PARAM = 'start'
END_DATE_PARAM = 'end'

@login_required
def members(request):
	if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', args=[], kwargs={'username':request.user.username}))
	plans = []
	member_count = 0
	for plan in MembershipPlan.objects.all():
		member_list = Member.objects.members_by_plan_id(plan.id);
		member_count = member_count + len(member_list)
		plans.append({ 'name':plan.name, 'id':plan.id, 'members':member_list, 'count':len(Member.objects.members_by_plan_id(plan.id))})
	return render_to_response('staff/members.html', { 'plans': plans, 'member_count':member_count }, context_instance=RequestContext(request))

def member_bcc(request, plan_id):
	plans = MembershipPlan.objects.all()
	if plan_id == '0':
		plan_name = 'All'
		member_list = Member.objects.active_members()
	else:
		plan_name = MembershipPlan.objects.get(pk=plan_id)
		member_list = Member.objects.members_by_plan_id(plan_id);
	return render_to_response('staff/member_bcc.html', { 'plans':plans, 'plan':plan_name, 'members':member_list }, context_instance=RequestContext(request))

@staff_member_required
def export_members(request):
	members = Member.objects.all()
	return render_to_response('staff/memberList.csv', { 'member_list': members }, context_instance=RequestContext(request))

@staff_member_required
def security_deposits(request):
	members = []
	total_deposits = 0;
	for membership in Membership.objects.filter(deposit_amount__gt=0):
		members.append({'id':membership.member.id, 'name':membership.member, 'deposit':membership.deposit_amount})
		total_deposits = total_deposits + membership.deposit_amount
	return render_to_response('staff/security_deposits.html', { 'member_list': members, 'total_deposits':total_deposits}, context_instance=RequestContext(request))

@staff_member_required
def signup(request):
	page_message = None
	if request.method == 'POST':
		member_signup_form = MemberSignupForm(request.POST, request.FILES)
		if member_signup_form.is_valid():
			user = member_signup_form.save()
			page_message = 'The user was successfully created: [<a href="%s">see detail</a>]' % (user.get_absolute_url())
			member_signup_form = MemberSignupForm()
	else:
		member_signup_form = MemberSignupForm()
		
	return render_to_response('staff/signup.html', { 'member_signup_form':member_signup_form, 'page_message':page_message }, context_instance=RequestContext(request))

@staff_member_required
def member_search(request):
	search_results = None
	if request.method == "POST":
		member_search_form = MemberSearchForm(request.POST)
		if member_search_form.is_valid(): 
			search_results = Member.objects.search(member_search_form.cleaned_data['terms'])
			if len(search_results) == 1:
				return HttpResponseRedirect(reverse('staff.views.member_detail', args=[], kwargs={'member_id':search_results[0].id}))
	else:
		member_search_form = MemberSearchForm()
	return render_to_response('staff/member_search.html', { 'member_search_form':member_search_form, 'search_results':search_results }, context_instance=RequestContext(request))

@staff_member_required
def transactions(request):
	page_message = None
	start, end = date_range_from_request(request)
	date_range_form = DateRangeForm({START_DATE_PARAM:start, END_DATE_PARAM:end })
	transactions = Transaction.objects.filter(created__range=(start, end)).order_by('-created')
	return render_to_response('staff/transactions.html', { "transactions":transactions, 'date_range_form':date_range_form, 'page_message':page_message }, context_instance=RequestContext(request))

@staff_member_required
def transaction(request, id):
	transaction = get_object_or_404(Transaction, pk=id)
	return render_to_response('staff/transaction.html', { "transaction":transaction }, context_instance=RequestContext(request))

def run_billing(request):
	page_message = None
	run_billing_form = RunBillingForm(initial={'run_billing':True})
	if request.method == 'POST':
		run_billing_form = RunBillingForm(request.POST)
		if run_billing_form.is_valid():
			billing.run_billing()
			page_message = 'At your request, I have run <a href="%s">the bills</a>.' % (reverse('staff.views.bills', args=[], kwargs={}),)
	return render_to_response('staff/run_billing.html', { 'run_billing_form':run_billing_form, 'page_message':page_message, "billing_logs":BillingLog.objects.all() }, context_instance=RequestContext(request))

@staff_member_required
def bills(request):
	page_message = None
	if request.method == 'POST':
		pay_bills_form = PayBillsForm(request.POST)
		if pay_bills_form.is_valid():
			try:
				member = Member.objects.get(pk=int(pay_bills_form.cleaned_data['member_id']))
			except:
				page_message = 'Error: I could not find that user.'

			amount = pay_bills_form.cleaned_data['amount']
			if page_message == None:
				bill_ids = [int(bill_id) for bill_id in request.POST.getlist('bill_id')]
				transaction = Transaction(member=member, status='closed', amount=Decimal(amount))
				transaction.note = pay_bills_form.cleaned_data['transaction_note']
				transaction.save()
				for bill in member.open_bills():
					if bill.id in bill_ids:
						transaction.bills.add(bill)
				page_message = 'Created a <a href="%s">transaction for %s</a>' % (reverse('staff.views.transaction', args=[], kwargs={'id':transaction.id}), member,)

	members = Member.objects.filter(models.Q(bills__isnull=False, bills__transactions=None, bills__paid_by__isnull=True) | models.Q(guest_bills__isnull=False, guest_bills__transactions=None)).distinct().order_by('user__last_name')
	invalids = Member.objects.active_members().filter(valid_billing=False)	
	return render_to_response('staff/bills.html', { "members":members, 'page_message':page_message, 'invalid_members':invalids }, context_instance=RequestContext(request))

@staff_member_required
def toggle_billing_flag(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	user = member.user
	
	page_message = member.full_name + " billing profile: "
	if member.valid_billing:
		page_message += " Invalid";
		member.valid_billing = False;
		member.save()
		email.send_invalid_billing(user)
	else:
		page_message += " Valid";
		member.valid_billing = True;
		member.save()
		
	if 'back' in request.POST:
		return HttpResponseRedirect(request.POST.get('back'))
	return HttpResponseRedirect(reverse('staff.views.bills'))

@staff_member_required
def bill(request, id):
	bill = get_object_or_404(Bill, pk=id)
	return render_to_response('staff/bill.html', { "bill":bill, 'new_member_deposit':settings.NEW_MEMBER_DEPOSIT }, context_instance=RequestContext(request))

@staff_member_required
def exit_task(request, id):
	task = get_object_or_404(ExitTask, pk=id)
	if request.method == 'POST':
		if 'save_exit_task' in request.POST:
			task = ExitTask.objects.get(pk=request.POST.get('task_id'))
			member = Member.objects.get(user__username=request.POST.get('username'))
			ExitTaskCompleted.objects.create(member=member, task=task)
			return HttpResponseRedirect(reverse('staff.views.exit_task', kwargs={ 'id':id }))
		elif 'Mark All' in request.POST:
			for member in task.uncompleted_members():
				update = ExitTaskCompleted.objects.create(member=member, task=task)
			return HttpResponseRedirect(reverse('staff.views.exit_task', kwargs={ 'id':id }))
	return render_to_response('staff/exit_task.html', {'task': task }, context_instance=RequestContext(request))

@staff_member_required
def onboard_task(request, id):
	task = get_object_or_404(Onboard_Task, pk=id)
	if request.method == 'POST':
		if 'save_onboard_task' in request.POST:
			task = Onboard_Task.objects.get(pk=request.POST.get('task_id'))
			member = Member.objects.get(user__username=request.POST.get('username'))
			Onboard_Task_Completed.objects.create(member=member, task=task)
			return HttpResponseRedirect(reverse('staff.views.onboard_task', kwargs={ 'id':id }))
		elif 'Mark All' in request.POST:
			for member in task.uncompleted_members():
				update = Onboard_Task_Completed.objects.create(member=member, task=task)
			return HttpResponseRedirect(reverse('staff.views.onboard_task', kwargs={ 'id':id }))
	return render_to_response('staff/onboard_task.html', {'task': task}, context_instance=RequestContext(request))

@staff_member_required
def todo(request) :			
	# Group & count by task
	onboard_tasks = []
	for task in Onboard_Task.objects.all().order_by('order'):
		onboard_tasks.append((task, len(task.uncompleted_members())))

	exit_tasks = []
	for task in ExitTask.objects.all().order_by('order'):
		exit_tasks.append((task, len(task.uncompleted_members())))
	
	return render_to_response('staff/todo.html', {'onboard_tasks':onboard_tasks, 'exit_tasks':exit_tasks, 'member_search_form':MemberSearchForm() }, context_instance=RequestContext(request))

@staff_member_required
def stats(request):		 
	# Group the daily logs into months
	daily_logs_by_month = []
	number_dict = {'month':'firstrun'}
	for daily_log in DailyLog.objects.all().order_by('visit_date').reverse():
		month = '%(year)i-%(month)i' % {'year':daily_log.visit_date.year, "month": daily_log.visit_date.month}
		if number_dict['month'] != month:
			if number_dict['month'] != 'firstrun':
				daily_logs_by_month.append(number_dict)
			number_dict = {'month':month, 'Bill':0, 'Trial':0, 'Waved':0, 'total':1}
			number_dict[daily_log.payment] = 1
		else:
			number_dict['total'] = number_dict['total'] + 1;
			if number_dict.has_key(daily_log.payment):
				number_dict[daily_log.payment] = number_dict[daily_log.payment] + 1

	return render_to_response('staff/stats.html', {'daily_logs_by_month':daily_logs_by_month}, context_instance=RequestContext(request))

def beginning_of_next_month(the_date):
	if the_date.month == 12:
		result = date(the_date.year + 1, 1, 1)
	else:
		result = date(the_date.year, the_date.month + 1, 1)
	return result

def first_days_in_months(start_date, end_date):
	"""Returns an array of dates which are the first day in each month starting at start_date's month and ending with the month after end_date's month"""
	if start_date.year == end_date.year and start_date.month == end_date.month: return [date(start_date.year, start_date.month, 1)]

	first_date = date(start_date.year, start_date.month, 1)
	
	results = [first_date]
	while beginning_of_next_month(results[-1]) < end_date: results.append(beginning_of_next_month(results[-1]))
	return results

class MonthHistory:
	def __init__(self, year, month):
		self.year = year
		self.month = month
		self.title = '%s-%s' % (self.month, self.year)
		self.start_date = date(year=year, month=month, day=1)
		start_day, self.days_in_month = calendar.monthrange(year, month)
		self.end_date = self.start_date + timedelta(self.days_in_month - 1)

		self.data = {} # str:str key:values for the month

@staff_member_required
def stats_membership_history(request):
	if 'start_date' in request.REQUEST:
		try:
			start_date = datetime.datetime.strptime(request.REQUEST.get('start_date'), "%m-%Y").date()
		except:
			return render_to_response('staff/stats_membership_history.html', { 'page_message':"Invalid Start Date!  Example: '01-2012'."}, context_instance=RequestContext(request))
	else:
		#start_date = min(DailyLog.objects.all().order_by('visit_date')[0].visit_date, Membership.objects.all().order_by('start_date')[0].start_date)
		start_date = date.today() - timedelta(days=365)
	start_month = date(year=start_date.year, month=start_date.month, day=1)
	end_date = date.today()
	end_month = date(year=end_date.year, month=end_date.month, day=1)

	average_only = 'average_only' in request.REQUEST
	working_month = start_month
	month_histories = []
	while working_month <= end_month:
		month_history = MonthHistory(working_month.year, working_month.month)
		month_histories.append(month_history)
		working_month = working_month + timedelta(days=month_history.days_in_month)

	for month in month_histories:
		dates = [date(month.year, month.month, i) for i in range(1, month.days_in_month + 1)]

		for plan in MembershipPlan.objects.all():
			data = calculate_monthly_low_high(plan.id, dates)
			if average_only:
				month.data[plan.name] = data[2]
			else:
				month.data[plan.name] = '%s - %s' % (data[0], data[1])

		month.data['visits'], month.data['trial'], month.data['waved'], month.data['billed'] = calculate_dropins(month.start_date, month.end_date)

		year_histories = []
		current_year = -1
		for month in month_histories:			  
			if month.year != current_year:
				year_histories.append([])
				current_year = month.year
			year_histories[-1].append(month)

	return render_to_response('staff/stats_membership_history.html', { 'history_types':sorted(month_histories[0].data.keys()), 
		'year_histories':year_histories, 'start_date':start_date, 'average_only':average_only
 	}, context_instance=RequestContext(request))

def calculate_dropins(start_date, end_date):
	all_logs = DailyLog.objects.filter(visit_date__gte=start_date, visit_date__lte=end_date)
	return (all_logs.filter(payment='Visit').distinct().count(), all_logs.filter(payment='Trial').distinct().count(), all_logs.filter(payment='Waved').distinct().count(), all_logs.filter(payment='Bill').distinct().count())

def calculate_monthly_low_high(plan_id, dates):
	"""returns a tuple of (min, max) for number of memberships in the date range of dates"""
	high = 0
	low = 100000000
	for working_date in dates:
		num_residents = Membership.objects.by_date(working_date).filter(membership_plan=plan_id).count()
		high = max(high, num_residents)
		low = min(low, num_residents)
		avg = int(round((low + high) / 2))
	return (low, high, avg)

@staff_member_required
def stats_history(request):		
	logs = [log for log in Membership.objects.all()]
	end_date = date.today()
	if len(logs) > 0:
		start_date = logs[0].start_date
	else:
		start_date = end_date
		
	monthly_stats = [{'start_date':d, 'end_date':beginning_of_next_month(d) - timedelta(days=1)} for d in first_days_in_months(start_date, end_date)]
	for stat in monthly_stats:
		stat['monthly_total'] = Membership.objects.by_date(stat['end_date']).count()
		stat['started'] = Membership.objects.filter(start_date__range=(stat['start_date'], stat['end_date'])).count()
		stat['ended'] = Membership.objects.filter(end_date__range=(stat['start_date'], stat['end_date'])).count()
	monthly_stats.reverse()
	return render_to_response('staff/stats_history.html', { 'monthly_stats':monthly_stats }, context_instance=RequestContext(request))

@staff_member_required
def stats_monthly(request):		
	# Pull all the monthly members
	memberships = Membership.objects.filter(end_date__isnull=True).order_by('start_date')
	total_income = 0
	for membership in memberships:
		total_income = total_income + membership.monthly_rate
	return render_to_response('staff/stats_monthly.html', {'memberships':memberships, 'total_income': total_income}, context_instance=RequestContext(request))

@staff_member_required
def stats_neighborhood(request):
	active_only = 'ActiveOnly' in request.POST
	
	member_count = Member.objects.member_count(active_only)
	specified_count = 0
	neighborhoods = []
	for hood in Neighborhood.objects.all():
		members = Member.objects.members_by_neighborhood(hood, active_only)
		specified_count = specified_count + members.count()
		neighborhoods.append({ 'name':hood.name, 'id':hood.id, 'members':members, 'count':members.count(), 'perc':(100*members.count())/member_count})
	
	# Group all our statistics into a dictionary
	stats_dict={ 'member_count':member_count, 'specified_count':specified_count, 'unknown_count':member_count-specified_count,
					 'specified_perc': 100*specified_count/member_count, 'unknown_perc': 100*(member_count-specified_count)/member_count}
	
	return render_to_response('staff/stats_neighborhood.html', { 'neighborhoods': neighborhoods, 'stats': stats_dict, 
									  'active_only': active_only}, context_instance=RequestContext(request))

@staff_member_required
def stats_membership_days(request):
	MembershipDays = namedtuple('MembershipDays', 'user, membership_count, total_days, daily_logs, max_days, current')
	membership_days = []
	users = User.objects.all()
	memberships = Membership.objects.select_related('member', 'member__user').all()
	avg_count = 0
	avg_total = 0
	for user in users:
		user_memberships = [m for m in memberships if m.member.user == user]
		membership_count = len(user_memberships)
		total_days = 0
		max_days = 0
		current = False;
		for membership in user_memberships:
			end = membership.end_date
			if not end: 
				end = date.today()
				current = True;
			diff = end - membership.start_date
			days = diff.days
			total_days = total_days + days
			if (days > max_days):
				max_days = days
		daily_logs = DailyLog.objects.filter(member=user.profile).count()
		membership_days.append(MembershipDays(user, membership_count, total_days, daily_logs, max_days, current))
		if total_days > 0:
			avg_count = avg_count + 1
			avg_total = avg_total + total_days
	membership_days.sort(key=lambda x:x.total_days, reverse=True)
	return render_to_response('staff/stats_membership_days.html', { 'membership_days':membership_days, 'avg_days':avg_total/avg_count }, context_instance=RequestContext(request))

@staff_member_required
def stats_gender(request):
	active_only = False
	if 'ActiveOnly' in request.POST or request.method == 'GET':
		active_only = True
	
	if active_only:
		m = Member.objects.active_members().filter(gender='M').count()
		f = Member.objects.active_members().filter(gender='F').count()
		o = Member.objects.active_members().filter(gender='O').count()
		u = Member.objects.active_members().filter(gender='U').count()
	else:
		m = Member.objects.filter(gender='M').count()
		f = Member.objects.filter(gender='F').count()
		o = Member.objects.filter(gender='O').count()
		u = Member.objects.filter(gender='U').count()
		
	t = m + f + o + u
	counts = { 'male':m, 'female':f, 'other':o, 'unknown':u, 'total':t }
	percentages = { 'male':p(m, t), 'female':p(f, t), 'other':p(o, t), 'unknown':p(u, t) }

	return render_to_response('staff/stats_gender.html', {'counts':counts, 'percentages':percentages, 'active_only':active_only}, context_instance=RequestContext(request))

def p(p, w):
	return int(round(100*(float(p)/float(w))))
	
@staff_member_required
def member_detail(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	daily_logs = DailyLog.objects.filter(member=member).order_by('visit_date').reverse()
	memberships = Membership.objects.filter(member=member).order_by('start_date').reverse()

	if request.method == 'POST':
		if 'save_onboard_task' in request.POST:
			task = Onboard_Task.objects.get(pk=request.POST.get('task_id'))
			Onboard_Task_Completed.objects.create(member=member, task=task)
		elif 'save_exit_task' in request.POST:
			task = ExitTask.objects.get(pk=request.POST.get('task_id'))
			ExitTaskCompleted.objects.create(member=member, task=task)
		else:
			print request.POST

	return render_to_response('staff/member_detail.html', { 'member':member, 'settings':settings}, context_instance=RequestContext(request))

def date_range_from_request(request):
	# Pull the Start Date param
	start = request.POST.get(START_DATE_PARAM, None)
	if not start: start = request.GET.get(START_DATE_PARAM, None)
	if not start:
		start_date = date.today() - timedelta(days=31)
		start = start_date.isoformat()
	end = request.POST.get(END_DATE_PARAM, None)
	if not end: end = request.GET.get(END_DATE_PARAM, None)
	if not end:
		end = date.today().isoformat()
	return (start, end)

@staff_member_required
def activity(request):
	start, end = date_range_from_request(request)
	date_range_form = DateRangeForm({START_DATE_PARAM:start, END_DATE_PARAM:end })
	starteo = timeo.strptime(start, "%Y-%m-%d")
	start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
	endeo = timeo.strptime(end, "%Y-%m-%d")
	end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
	days = [{'date':start_date + timedelta(days=i)} for i in range((end_date - start_date).days) ]
	for day in days:
		day['daily_logs'] = DailyLog.objects.filter(visit_date=day['date']).count()
		day['membership'] = Membership.objects.by_date(day['date']).count()
		day['has_desk'] = Membership.objects.by_date(day['date']).filter(has_desk=True).count()
		day['occupancy'] = day['daily_logs'] + day['has_desk']

	max_membership = 0
	max_has_desk = 0
	max_daily_logs = 0
	max_total = 0
	total_daily_logs = 0
	for day in days:
		max_membership = max(max_membership, day['membership'])
		max_has_desk = max(max_has_desk, day['has_desk'])
		max_daily_logs = max(max_daily_logs, day['daily_logs'])
		max_total = max(max_total, day['membership'] + day['daily_logs'])
		total_daily_logs = total_daily_logs + day['daily_logs']
		
	graph_size = 200 # this is lame, but damn easy
	for day in days:
		if max_has_desk > 0:
			day['has_desk_percentage'] = int(day['has_desk'] / float(max_has_desk) * 100)
			day['has_desk_size'] = int(graph_size * day['has_desk'] / float(max_has_desk + max_daily_logs))
			day['has_desk_size_negative'] = graph_size - day['has_desk_size']
		if max_membership > 0:
			day['membership_percentage'] = int(day['membership'] / float(max_membership) * 100)
			day['membership_size'] = int(graph_size * day['membership'] / float(max_membership))
			day['membership_size_negative'] = graph_size - day['membership_size']
		if max_daily_logs > 0:
			day['daily_logs_percentage'] = int(day['daily_logs'] / float(max_daily_logs) * 100)
			day['daily_logs_size'] = int(graph_size * day['daily_logs'] / float(max_daily_logs))
			day['daily_logs_size_negative'] = graph_size - day['daily_logs_size']
	return render_to_response('staff/activity.html', {'days':days, 'graph_size':graph_size, 'max_has_desk':max_has_desk, 'max_membership':max_membership, 'max_daily_logs':max_daily_logs, 'max_total':max_total, 'total_daily_logs': total_daily_logs, 'date_range_form':date_range_form, 'start':start, 'end':end }, context_instance=RequestContext(request))


@staff_member_required
def activity_list(request):
	start, end = date_range_from_request(request)
	date_range_form = DateRangeForm({START_DATE_PARAM:start, END_DATE_PARAM:end })
	starteo = timeo.strptime(start, "%Y-%m-%d")
	start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
	endeo = timeo.strptime(end, "%Y-%m-%d")
	end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
	daily_logs = DailyLog.objects.filter(visit_date__range=(start_date, end_date))
	return render_to_response('staff/activity_list.html', {'daily_logs':daily_logs, 'date_range_form':date_range_form, 'start_date':start_date, 'end_date':end_date }, context_instance=RequestContext(request))

@staff_member_required
def activity_date(request, year, month, day):
	activity_date = date(year=int(year), month=int(month), day=int(day))
	return activity_for_date(request, activity_date)

@staff_member_required
def activity_today(request):
	return activity_for_date(request, datetime.date.today())

@staff_member_required
def activity_for_date(request, activity_date):
	daily_logs = DailyLog.objects.filter(visit_date=activity_date).reverse()

	page_message = None
	if request.method == 'POST':
		daily_log_form = DailyLogForm(request.POST, request.FILES)
		if daily_log_form.is_valid():
			page_message = 'Activity was recorded!'
			daily_log_form.save()
	else:
		daily_log_form = DailyLogForm(initial={'visit_date': activity_date})
	
	return render_to_response('staff/activity_date.html', {'daily_logs':daily_logs, 'daily_log_form':daily_log_form, 'page_message':page_message, 'activity_date':activity_date, 'next_date':activity_date + timedelta(days=1), 'previous_date':activity_date - timedelta(days=1),  }, context_instance=RequestContext(request))

@staff_member_required
def member_transactions(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	return render_to_response('staff/member_transactions.html', {'member':member}, context_instance=RequestContext(request))

@staff_member_required
def member_bills(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	return render_to_response('staff/member_bills.html', {'member':member}, context_instance=RequestContext(request))

@staff_member_required
def member_activity(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	payment_types = ['Visit', 'Trial', 'Waved', 'Bill']
	return render_to_response('staff/member_activity.html', {'payment_types':payment_types, 'member':member}, context_instance=RequestContext(request))

@staff_member_required
def member_membership(request, member_id):
	member = get_object_or_404(Member, pk=member_id)
	
	if request.method == 'POST':
		membership_form = MembershipForm(request.POST, request.FILES)
		if membership_form.is_valid():
			membership_form.save()
			return HttpResponseRedirect(reverse('staff.views.member_detail', args=[], kwargs={'member_id':member.id}))
	
	# Send them to the update page if we don't have an end date
	if (member.last_membership() and not member.last_membership().end_date):
		return HttpResponseRedirect(reverse('staff.views.membership', args=[], kwargs={'membership_id':member.last_membership().id}))
	
	return render_to_response('staff/membership.html', {'member':member, 'membership_plans':MembershipPlan.objects.all(), 
		'membership_form':MembershipForm(initial={'member':member_id}), 'today':date.today().isoformat()}, context_instance=RequestContext(request))

@staff_member_required
def membership(request, membership_id):
	membership = get_object_or_404(Membership, pk=membership_id)
	
	if request.method == 'POST':
		membership_form = MembershipForm(request.POST, request.FILES)
		if membership_form.is_valid():
			membership_form.save()
			return HttpResponseRedirect(reverse('staff.views.member_detail', args=[], kwargs={'member_id':membership.member.id}))
	else:
		membership_form = MembershipForm(initial={'membership_id':membership.id, 'member':membership.member.id, 'membership_plan':membership.membership_plan, 
			'start_date':membership.start_date, 'end_date':membership.end_date, 'monthly_rate':membership.monthly_rate, 'dropin_allowance':membership.dropin_allowance, 
			'daily_rate':membership.daily_rate, 'deposit_amount':membership.deposit_amount, 'has_desk':membership.has_desk, 'guest_of':membership.guest_of, 'note':membership.note})

	return render_to_response('staff/membership.html', {'member':membership.member, 'membership': membership, 'membership_plans':MembershipPlan.objects.all(), 
		'membership_form':membership_form, 'today':date.today().isoformat()}, context_instance=RequestContext(request))

@staff_member_required
def view_user_reports(request):
	if request.method == 'POST':
		form = user_reports.UserReportForm(request.POST, request.FILES)
	else:
		form = user_reports.getDefaultForm()

	report = user_reports.User_Report(form)
	users = report.get_users()
	return render_to_response('staff/user_reports.html', {'users':users, 'form':form}, context_instance=RequestContext(request))

# Copyright 2009, 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
