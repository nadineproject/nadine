import calendar
from datetime import date, datetime, timedelta
from collections import namedtuple

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils.timezone import localtime, now

from nadine.models.core import Neighborhood
from nadine.models.membership import Membership, MembershipPackage, ResourceSubscription
from nadine.models.usage import CoworkingDay
from nadine.forms import DateRangeForm


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
    all_logs = CoworkingDay.objects.filter(visit_date__gte=start_date, visit_date__lte=end_date)
    return (all_logs.filter(payment='Visit').distinct().count(), all_logs.filter(payment='Trial').distinct().count(), all_logs.filter(payment='Waive').distinct().count(), all_logs.filter(payment='Bill').distinct().count())


def calculate_monthly_low_high(package, dates):
    """returns a tuple of (min, max) for number of memberships in the date range of dates"""
    high = 0
    low = 100000000
    for working_date in dates:
        num_residents = User.helper.members_by_package(package, working_date).count()
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
def daily(request):
    # Group the daily logs into months
    daily_logs_by_month = []
    number_dict = {'month': 'firstrun'}
    for daily_log in CoworkingDay.objects.all().order_by('visit_date').reverse():
        month = '%(year)i-%(month)i' % {'year': daily_log.visit_date.year, "month": daily_log.visit_date.month}
        if number_dict['month'] != month:
            if number_dict['month'] != 'firstrun':
                daily_logs_by_month.append(number_dict)
            number_dict = {'month': month, 'Bill': 0, 'Trial': 0, 'Waive': 0, 'total': 1}
            number_dict[daily_log.payment] = 1
        else:
            number_dict['total'] = number_dict['total'] + 1
            if daily_log.payment in number_dict:
                number_dict[daily_log.payment] = number_dict[daily_log.payment] + 1

    return render(request, 'staff/stats/daily.html', {'daily_logs_by_month': daily_logs_by_month})


@staff_member_required
def memberships(request):
    if 'start_date' in request.POST:
        try:
            start_date = datetime.strptime(request.POST.get('start_date'), "%m-%Y").date()
        except:
            messages.error(request, "Invalid Start Date!  Example: '01-2012'.")
            return render(request, 'staff/stats/memberships.html', {})
    else:
        start_date = localtime(now()).date() - timedelta(days=365)
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

        for package in MembershipPackage.objects.filter(enabled=True):
            data = calculate_monthly_low_high(package, dates)
            if average_only:
                month.data[package.name] = data[2]
            else:
                month.data[package.name] = '%s - %s' % (data[0], data[1])

        month.data['visits'], month.data['trial'], month.data['waive'], month.data['billed'] = calculate_dropins(month.start_date, month.end_date)

        year_histories = []
        current_year = -1
        for month in month_histories:
            if month.year != current_year:
                year_histories.append([])
                current_year = month.year
            year_histories[-1].append(month)

    context = {'history_types': sorted(month_histories[0].data.keys()),
        'year_histories': year_histories, 'start_date': start_date, 'average_only': average_only}
    return render(request, 'staff/stats/memberships.html', context)


@staff_member_required
def history(request):
    date_range_form = DateRangeForm.from_request(request, days=365)
    start_date, end_date = date_range_form.get_dates()
    logs = [log for log in Membership.objects.all()]
    monthly_stats = [{'start_date': d, 'end_date': beginning_of_next_month(d) - timedelta(days=1)} for d in first_days_in_months(start_date, end_date)]
    for stat in monthly_stats:
        stat['monthly_total'] = Membership.objects.active_memberships(stat['end_date']).count()
        stat['started'] = Membership.objects.date_range(start=stat['start_date'], end=stat['end_date'], action='started').count()
        stat['ended'] = Membership.objects.date_range(start=stat['start_date'], end=stat['end_date'], action='ended').count()
    monthly_stats.reverse()
    context = {'monthly_stats': monthly_stats,
               'date_range_form': date_range_form,
               'start_date': start_date,
               'end_date': end_date}
    return render(request, 'staff/stats/history.html', context)


@staff_member_required
def monthly(request):
    # Pull all the monthly members
    memberships = Membership.objects.active_individual_memberships()
    # memberships = Membership.objects.filter(end_date__isnull=True).order_by('start_date')
    total_income = 0
    # for membership in memberships:
    #     total_income = total_income + membership.monthly_rate
    context = {'memberships': memberships, 'total_income': total_income}
    return render(request, 'staff/stats/monthly.html', context)


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
        users = User.helper.members_by_neighborhood(hood, active_only)
        specified_count = specified_count + users.count()
        neighborhoods.append({'name': hood.name,
                              'id': hood.id,
                              'users': users,
                              'count': users.count(),
                              'perc': (100 * users.count()) / total_count})

    # Group all our statistics into a dictionary
    stats_dict = {'member_count': total_count,
                  'specified_count': specified_count,
                  'unknown_count': total_count - specified_count,
                  'specified_perc': 100 * specified_count / total_count, 'unknown_perc': 100 * (total_count - specified_count) / total_count}

    context = {'neighborhoods': neighborhoods, 'stats': stats_dict, 'active_only': active_only}
    return render(request, 'staff/stats/neighborhood.html', context)


@staff_member_required
def longevity(request):
    MembershipDays = namedtuple('MembershipDays', 'user, membership_count, total_days, daily_logs, max_days, current')
    membership_days = []
    users = User.objects.all()
    memberships =  ResourceSubscription.objects.all_subscriptions_by_member()
    avg_count = 0
    avg_total = 0
    for user in users:
        # Currently count all days of all subscriptions. We need unique days
        user_subscriptions = [m for m in memberships if m.username == user.username]
        subscription_count = len(user_subscriptions)
        total_days = 0
        max_days = 0
        current = False
        starts = []
        for sub in user_subscriptions:
            end = sub.end_date
            if not end:
                end = localtime(now()).date()
                current = True
            dates = (sub.start_date, end)
            starts.append(dates)
        date_set = set(starts)
        for d in date_set:
            diff = d[1] - d[0]
            days = diff.days
            total_days = total_days + days
            if (days > max_days):
                max_days = days
        daily_logs = CoworkingDay.objects.filter(user=user).count()
        membership_days.append(MembershipDays(user, subscription_count, total_days, daily_logs, max_days, current))
        if total_days > 0:
            avg_count = avg_count + 1
            avg_total = avg_total + total_days
    membership_days.sort(key=lambda x: x.total_days, reverse=True)
    context = {'membership_days': membership_days, 'avg_days': avg_total / avg_count}
    return render(request, 'staff/stats/longevity.html', context)


@staff_member_required
def gender(request):
    active_only = False
    if 'ActiveOnly' in request.POST or request.method == 'GET':
        active_only = True

    if active_only:
        users = User.helper.active_members()
    else:
        users = User.objects.all()

    m = users.filter(profile__gender='M').count()
    f = users.filter(profile__gender='F').count()
    o = users.filter(profile__gender='O').count()
    u = users.filter(profile__gender='U').count()

    t = m + f + o + u
    counts = {'male': m, 'female': f, 'other': o, 'unknown': u, 'total': t}
    percentages = {'male': p(m, t), 'female': p(f, t), 'other': p(o, t), 'unknown': p(u, t)}

    context = {'counts': counts, 'percentages': percentages,
        'active_only': active_only}
    return render(request, 'staff/stats/gender.html', context)


@staff_member_required
def graph(request):
    graph = request.POST.get("graph", "members")
    date_range_form = DateRangeForm.from_request(request, days=30)
    start_date, end_date = date_range_form.get_dates()
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
    context = {
        'title':title,
        'graph':graph,
        'days': days,
        'date_range_form': date_range_form,
        'start_date': start_date, 'end_date': end_date,
        'min': min_v, 'max': max_v, 'avg': avg_v,
    }
    return render(request, 'staff/stats/graph.html', context)


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
            membership_income = membership_income + membership.monthly_rate()
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


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
