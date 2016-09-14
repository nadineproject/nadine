import calendar
import time as timeo
from datetime import date, datetime, timedelta
from collections import namedtuple

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

from nadine.models import Member, Membership, MembershipPlan, DailyLog, Neighborhood

from staff.views.activity import date_range_from_request, START_DATE_PARAM, END_DATE_PARAM
from staff.forms import DateRangeForm

################################################################################
# Helper Methods
################################################################################

def beginning_of_next_month(the_date):
    if the_date.month == 12:
        result = date(the_date.year + 1, 1, 1)
    else:
        result = date(the_date.year, the_date.month + 1, 1)
    return result


def first_days_in_months(start_date, end_date):
    """Returns an array of dates which are the first day in each month starting at start_date's month and ending with the month after end_date's month"""
    if start_date.year == end_date.year and start_date.month == end_date.month:
        return [date(start_date.year, start_date.month, 1)]

    first_date = date(start_date.year, start_date.month, 1)

    results = [first_date]
    while beginning_of_next_month(results[-1]) < end_date:
        results.append(beginning_of_next_month(results[-1]))
    return results


class MonthHistory:

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.title = '%s-%s' % (self.month, self.year)
        self.start_date = date(year=year, month=month, day=1)
        start_day, self.days_in_month = calendar.monthrange(year, month)
        self.end_date = self.start_date + timedelta(self.days_in_month - 1)

        self.data = {}  # str:str key:values for the month


def calculate_dropins(start_date, end_date):
    all_logs = DailyLog.objects.filter(visit_date__gte=start_date, visit_date__lte=end_date)
    return (all_logs.filter(payment='Visit').distinct().count(), all_logs.filter(payment='Trial').distinct().count(), all_logs.filter(payment='Waive').distinct().count(), all_logs.filter(payment='Bill').distinct().count())


def calculate_monthly_low_high(plan_id, dates):
    """returns a tuple of (min, max) for number of memberships in the date range of dates"""
    high = 0
    low = 100000000
    for working_date in dates:
        num_residents = Membership.objects.active_memberships(working_date).filter(membership_plan=plan_id).count()
        high = max(high, num_residents)
        low = min(low, num_residents)
        avg = int(round((low + high) / 2))
    return (low, high, avg)


def p(p, w):
    return int(round(100 * (float(p) / float(w))))


################################################################################
# Views
################################################################################

@staff_member_required
def stats(request):
    # Group the daily logs into months
    daily_logs_by_month = []
    number_dict = {'month': 'firstrun'}
    for daily_log in DailyLog.objects.all().order_by('visit_date').reverse():
        month = '%(year)i-%(month)i' % {'year': daily_log.visit_date.year, "month": daily_log.visit_date.month}
        if number_dict['month'] != month:
            if number_dict['month'] != 'firstrun':
                daily_logs_by_month.append(number_dict)
            number_dict = {'month': month, 'Bill': 0, 'Trial': 0, 'Waive': 0, 'total': 1}
            number_dict[daily_log.payment] = 1
        else:
            number_dict['total'] = number_dict['total'] + 1
            if number_dict.has_key(daily_log.payment):
                number_dict[daily_log.payment] = number_dict[daily_log.payment] + 1

    return render_to_response('staff/stats.html', {'daily_logs_by_month': daily_logs_by_month}, context_instance=RequestContext(request))


@staff_member_required
def membership_history(request):
    if 'start_date' in request.POST:
        try:
            start_date = datetime.datetime.strptime(request.POST.get('start_date'), "%m-%Y").date()
        except:
            return render_to_response('staff/stats_membership_history.html', {'page_message': "Invalid Start Date!  Example: '01-2012'."}, context_instance=RequestContext(request))
    else:
        #start_date = min(DailyLog.objects.all().order_by('visit_date')[0].visit_date, Membership.objects.all().order_by('start_date')[0].start_date)
        start_date = timezone.now().date() - timedelta(days=365)
    start_month = date(year=start_date.year, month=start_date.month, day=1)
    end_date = timezone.now().date()
    end_month = date(year=end_date.year, month=end_date.month, day=1)

    average_only = 'average_only' in request.POST
    working_month = start_month
    month_histories = []
    while working_month <= end_month:
        month_history = MonthHistory(working_month.year, working_month.month)
        month_histories.append(month_history)
        working_month = working_month + timedelta(days=month_history.days_in_month)

    for month in month_histories:
        dates = [date(month.year, month.month, i) for i in range(1, month.days_in_month + 1)]

        for plan in MembershipPlan.objects.filter(enabled=True):
            data = calculate_monthly_low_high(plan.id, dates)
            if average_only:
                month.data[plan.name] = data[2]
            else:
                month.data[plan.name] = '%s - %s' % (data[0], data[1])

        month.data['visits'], month.data['trial'], month.data['waive'], month.data['billed'] = calculate_dropins(month.start_date, month.end_date)

        year_histories = []
        current_year = -1
        for month in month_histories:
            if month.year != current_year:
                year_histories.append([])
                current_year = month.year
            year_histories[-1].append(month)

    return render_to_response('staff/stats_membership_history.html', {'history_types': sorted(month_histories[0].data.keys()),
                                                                      'year_histories': year_histories, 'start_date': start_date, 'average_only': average_only
                                                                      }, context_instance=RequestContext(request))


@staff_member_required
def history(request):
    logs = [log for log in Membership.objects.all()]
    end_date = timezone.now().date()
    if len(logs) > 0:
        start_date = logs[0].start_date
    else:
        start_date = end_date

    monthly_stats = [{'start_date': d, 'end_date': beginning_of_next_month(d) - timedelta(days=1)} for d in first_days_in_months(start_date, end_date)]
    for stat in monthly_stats:
        stat['monthly_total'] = Membership.objects.active_memberships(stat['end_date']).count()
        stat['started'] = Membership.objects.filter(start_date__range=(stat['start_date'], stat['end_date'])).count()
        stat['ended'] = Membership.objects.filter(end_date__range=(stat['start_date'], stat['end_date'])).count()
    monthly_stats.reverse()
    return render_to_response('staff/stats_history.html', {'monthly_stats': monthly_stats}, context_instance=RequestContext(request))


@staff_member_required
def monthly(request):
    # Pull all the monthly members
    memberships = Membership.objects.filter(end_date__isnull=True).order_by('start_date')
    total_income = 0
    for membership in memberships:
        total_income = total_income + membership.monthly_rate
    return render_to_response('staff/stats_monthly.html', {'memberships': memberships, 'total_income': total_income}, context_instance=RequestContext(request))


@staff_member_required
def neighborhood(request):
    active_only = 'ActiveOnly' in request.POST

    if active_only:
        total_count = User.helper.active_members().count()
    else:
        total_count = User.objects.all().count()
    specified_count = 0
    neighborhoods = []
    for hood in Neighborhood.objects.all():
        members = Member.objects.members_by_neighborhood(hood, active_only)
        specified_count = specified_count + members.count()
        neighborhoods.append({'name': hood.name, 'id': hood.id, 'members': members, 'count': members.count(), 'perc': (100 * members.count()) / total_count})

    # Group all our statistics into a dictionary
    stats_dict = {'member_count': total_count, 'specified_count': specified_count, 'unknown_count': total_count - specified_count,
                  'specified_perc': 100 * specified_count / total_count, 'unknown_perc': 100 * (total_count - specified_count) / total_count}

    return render_to_response('staff/stats_neighborhood.html', {'neighborhoods': neighborhoods, 'stats': stats_dict,
                                                                'active_only': active_only}, context_instance=RequestContext(request))


@staff_member_required
def membership_days(request):
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
        current = False
        for membership in user_memberships:
            end = membership.end_date
            if not end:
                end = timezone.now().date()
                current = True
            diff = end - membership.start_date
            days = diff.days
            total_days = total_days + days
            if (days > max_days):
                max_days = days
        daily_logs = DailyLog.objects.filter(user=user).count()
        membership_days.append(MembershipDays(user, membership_count, total_days, daily_logs, max_days, current))
        if total_days > 0:
            avg_count = avg_count + 1
            avg_total = avg_total + total_days
    membership_days.sort(key=lambda x: x.total_days, reverse=True)
    return render_to_response('staff/stats_membership_days.html', {'membership_days': membership_days, 'avg_days': avg_total / avg_count}, context_instance=RequestContext(request))


@staff_member_required
def gender(request):
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
    counts = {'male': m, 'female': f, 'other': o, 'unknown': u, 'total': t}
    percentages = {'male': p(m, t), 'female': p(f, t), 'other': p(o, t), 'unknown': p(u, t)}

    return render_to_response('staff/stats_gender.html', {'counts': counts, 'percentages': percentages, 'active_only': active_only}, context_instance=RequestContext(request))


@staff_member_required
def graph(request):
    graph = request.POST.get("graph", "members")
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    starteo = timeo.strptime(start, "%Y-%m-%d")
    start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
    endeo = timeo.strptime(end, "%Y-%m-%d")
    end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)

    days = [{'date': start_date + timedelta(days=i)} for i in range((end_date - start_date).days)]
    if graph == "members":
        title = "Members by Day"
        min_v, max_v, avg_v, days = graph_members(days)
    elif graph == "income":
        title = "Monthly Membership Income by Day"
        min_v, max_v, avg_v, days = graph_income(days)
    elif graph == "amv":
        title = "Average Monthly Value"
        min_v, max_v, avg_v, days = graph_members(days)
    elif graph == "churn":
        title = "Membership Churn"


    return render_to_response('staff/stats_graph.html', {'title':title, 'graph':graph,
        'days': days, 'date_range_form': date_range_form, 'start': start, 'end': end,
        'min': min_v, 'max': max_v, 'avg': avg_v
    }, context_instance=RequestContext(request))


def graph_members(days):
    member_min = 0
    member_max = 0
    member_total = 0
    for day in days:
        day['value'] = Membership.objects.active_memberships(day['date']).count()
        member_total = member_total + day['value']
        if day['value'] > member_max:
            member_max = day['value']
        if member_min == 0 or day['value'] < member_min:
            member_min = day['value']
    member_avg = member_total / len(days)
    return (member_min, member_max, member_avg, days)


def graph_income(days):
    income_min = 0
    income_max = 0
    income_total = 0
    for day in days:
        membership_count = 0
        membership_income = 0
        for membership in Membership.objects.active_memberships(day['date']):
            membership_count = membership_count + 1
            membership_income = membership_income + membership.monthly_rate
        income_total = income_total + membership_income
        if membership_income > income_max:
            income_max = membership_income
        if income_min == 0 or membership_income < income_min:
            income_min = membership_income
        day['membership'] = membership_count
        day['value'] = membership_income
    income_avg = income_total / len(days)
    return (income_min, income_max, income_avg, days)


def graph_amv(days):
    min_v = max_v = avg_v = 100
    member_min = 0
    member_max = 0
    member_total = 0
    for day in days:
        day['value'] = Membership.objects.active_memberships(day['date']).count()
        member_total = member_total + day['value']
        if day['value'] > member_max:
            member_max = day['value']
        if member_min == 0 or day['value'] < member_min:
            member_min = day['value']
    member_avg = member_total / len(days)
    return (min_v, max_v, avg_v, days)
