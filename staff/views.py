import traceback
import time as timeo
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

import settings
from models import *
from forms import *
import billing

START_DATE_PARAM = 'start'
END_DATE_PARAM = 'end'

@login_required
def members(request):
   if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', args=[], kwargs={'username':request.user.username}))
   plans = []
   for plan_id, plan_name  in MONTHLY_PLAN_CHOICES:
      plans.append({ 'name':plan_name, 'id':plan_id, 'members':Member.objects.members_by_monthly_log_type(plan_id), 'count':len(Member.objects.members_by_monthly_log_type(plan_id))})
   return render_to_response('staff/members.html', { 'plans': plans, 'member_search_form':MemberSearchForm() }, context_instance=RequestContext(request))

@staff_member_required
def export_members(request):
   members = Member.objects.all()
   return render_to_response('staff/memberList.csv', { 'member_list': members }, context_instance=RequestContext(request))

@staff_member_required
def signup(request):
   page_message = None
   if request.method == 'POST':
      member_signup_form = MemberSignupForm(request.POST, request.FILES)
      if member_signup_form.is_valid():
         user = member_signup_form.save()
         page_message = 'The user was successfully created: [<a href="%s">see detail</a>], [<a href="%s">add daily log</a>] or [<a href="%s">add monthly log</a>]' % (user.get_absolute_url(), reverse('admin:staff_dailylog_add'), reverse('admin:staff_monthlylog_add'))
         member_signup_form = MemberSignupForm()
   else:
      member_signup_form = MemberSignupForm()
      
   return render_to_response('staff/signup.html', { 'member_signup_form':member_signup_form, 'page_message':page_message }, context_instance=RequestContext(request))

def daily_log(request):
   page_message = None
   if request.method == 'POST':
      daily_log_form = DailyLogForm(request.POST, request.FILES)
      if daily_log_form.is_valid():
         page_message = 'The daily log was created!'
         daily_log_form.save()
         daily_log_form = DailyLogForm()
   else:
      daily_log_form = DailyLogForm()

   return render_to_response('staff/dailylog.html', { 'daily_log_form':daily_log_form, 'page_message':page_message }, context_instance=RequestContext(request))

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
   return render_to_response('staff/bills.html', { "members":members, 'page_message':page_message }, context_instance=RequestContext(request))

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

@staff_member_required
def stats_history(request):      
   logs = [log for log in MonthlyLog.objects.all()]
   end_date = date.today()
   if len(logs) > 0:
      start_date = logs[0].start_date
   else:
      start_date = end_date
      
   monthly_stats = [{'start_date':d, 'end_date':beginning_of_next_month(d) - timedelta(days=1)} for d in first_days_in_months(start_date, end_date)]
   for stat in monthly_stats:
      stat['monthly_total'] = MonthlyLog.objects.by_date(stat['end_date']).count()
      stat['started'] = MonthlyLog.objects.filter(start_date__range=(stat['start_date'], stat['end_date'])).count()
      stat['ended'] = MonthlyLog.objects.filter(end_date__range=(stat['start_date'], stat['end_date'])).count()
   monthly_stats.reverse()
   return render_to_response('staff/stats_history.html', { 'monthly_stats':monthly_stats }, context_instance=RequestContext(request))

@staff_member_required
def stats_monthly(request):      
   # Pull all the monthly members
   monthly_logs = MonthlyLog.objects.filter(end_date__isnull=True).order_by('start_date')
   total_income = 0
   for log in monthly_logs:
      total_income = total_income + log.rate
   return render_to_response('staff/stats_monthly.html', {'monthly_logs':monthly_logs, 'total_income': total_income}, context_instance=RequestContext(request))

@staff_member_required
def stats_member_types(request):
   types_dict = {}
   for plan_id, plan_name in MONTHLY_PLAN_CHOICES:
      types_dict[plan_id] = len(Member.objects.members_by_monthly_log_type(plan_id))

   plan_ids = [t[0] for t in MONTHLY_PLAN_CHOICES]
   for member in Member.objects.all():
      type_id = member.membership_type()
      if type_id in plan_ids: continue
      if types_dict.has_key(type_id):
         types_dict[type_id] = types_dict[type_id] + 1
      else:
         types_dict[type_id] = 1
   return render_to_response('staff/stats_member_types.html', {'types_dict': types_dict, 'member_count': Member.objects.all().count()}, context_instance=RequestContext(request))

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
def member_detail(request, member_id):
   member = get_object_or_404(Member, pk=member_id)
   daily_logs = DailyLog.objects.filter(member=member).order_by('visit_date').reverse()
   monthly_logs = MonthlyLog.objects.filter(member=member).order_by('start_date').reverse()

   if request.method == 'POST':
      if 'save_onboard_task' in request.POST:
         task = Onboard_Task.objects.get(pk=request.POST.get('task_id'))
         Onboard_Task_Completed.objects.create(member=member, task=task)
      elif 'save_exit_task' in request.POST:
         task = ExitTask.objects.get(pk=request.POST.get('task_id'))
         ExitTaskCompleted.objects.create(member=member, task=task)
      else:
         print request.POST

   return render_to_response('staff/member_detail.html', { 'member':member }, context_instance=RequestContext(request))

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
      day['membership'] = MonthlyLog.objects.by_date(day['date']).count()
      day['residents'] = MonthlyLog.objects.by_date(day['date']).filter(plan='Resident').count()
      day['occupancy'] = day['daily_logs'] + day['residents']

   max_membership = 0
   max_residents = 0
   max_daily_logs = 0
   max_total = 0
   total_daily_logs = 0
   for day in days:
      max_membership = max(max_membership, day['membership'])
      max_residents = max(max_residents, day['residents'])
      max_daily_logs = max(max_daily_logs, day['daily_logs'])
      max_total = max(max_total, day['membership'] + day['daily_logs'])
      total_daily_logs = total_daily_logs + day['daily_logs']
      
   graph_size = 200 # this is lame, but damn easy
   for day in days:
      if max_residents > 0:
         day['residents_percentage'] = int(day['residents'] / float(max_residents) * 100)
         day['residents_size'] = int(graph_size * day['residents'] / float(max_residents + max_daily_logs))
         day['residents_size_negative'] = graph_size - day['residents_size']
      if max_membership > 0:
         day['membership_percentage'] = int(day['membership'] / float(max_membership) * 100)
         day['membership_size'] = int(graph_size * day['membership'] / float(max_membership))
         day['membership_size_negative'] = graph_size - day['membership_size']
      if max_daily_logs > 0:
         day['daily_logs_percentage'] = int(day['daily_logs'] / float(max_daily_logs) * 100)
         day['daily_logs_size'] = int(graph_size * day['daily_logs'] / float(max_daily_logs))
         day['daily_logs_size_negative'] = graph_size - day['daily_logs_size']
   return render_to_response('staff/activity.html', {'days':days, 'graph_size':graph_size, 'max_residents':max_residents, 'max_membership':max_membership, 'max_daily_logs':max_daily_logs, 'max_total':max_total, 'total_daily_logs': total_daily_logs, 'date_range_form':date_range_form, 'start':start, 'end':end }, context_instance=RequestContext(request))


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
   daily_logs = DailyLog.objects.filter(visit_date=activity_date)
   return render_to_response('staff/activity_date.html', {'daily_logs':daily_logs, 'activity_date':activity_date, 'next_date':activity_date + timedelta(days=1), 'previous_date':activity_date - timedelta(days=1) }, context_instance=RequestContext(request))

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

# Copyright 2009, 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
