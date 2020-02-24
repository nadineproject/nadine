from datetime import date, datetime, timedelta

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
from django.utils.timezone import localtime, now, get_current_timezone

from doors.keymaster.models import DoorEvent
from arpwatch.models import ArpLog
from nadine.forms import CoworkingDayForm, DateRangeForm
from nadine.models import CoworkingDay, Membership, ResourceSubscription


@staff_member_required
def graph(request):
    date_range_form = DateRangeForm.from_request(request, days=30)
    start_date, end_date = date_range_form.get_dates()
    days = [{'date': start_date + timedelta(days=i)} for i in range((end_date - start_date).days)]
    days.reverse()
    for day in days:
        memberships = Membership.objects.active_memberships(day['date'])
        day['daily_logs'] = CoworkingDay.objects.filter(visit_date=day['date']).count()
        day['has_desk'] = ResourceSubscription.objects.active_subscriptions(target_date=day['date']).filter(resource=3).count()
        day['occupancy'] = day['daily_logs'] + day['has_desk']
        day['membership'] = memberships.count()

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

    graph_size = 200  # this is lame, but damn easy
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
    context = {
        'days': days,
        'graph_size': graph_size,
        'max_has_desk': max_has_desk,
        'max_membership': max_membership,
        'max_daily_logs': max_daily_logs,
        'max_total': max_total,
        'total_daily_logs': total_daily_logs,
        'date_range_form': date_range_form,
    }
    return render(request, 'staff/activity/graph.html', context)


@staff_member_required
def list(request):
    date_range_form = DateRangeForm.from_request(request, days=30)
    start_date, end_date = date_range_form.get_dates()
    daily_logs = CoworkingDay.objects.filter(visit_date__range=(start_date, end_date))
    context = {
        'daily_logs': daily_logs,
        'date_range_form': date_range_form,
    }
    return render(request, 'staff/activity/list.html', context)


@staff_member_required
def activity_for_date(request, activity_date):
    activity = CoworkingDay.objects.filter(visit_date=activity_date).reverse()
    today = localtime(now()).date()
    activity_form = None

    if request.method == 'POST':
        if 'mark_waived' in request.POST:
            for visit in activity:
                if visit.billable:
                    visit.mark_waived()
            messages.success(request, 'All selected visits have been waived')
        else:
            activity_form = CoworkingDayForm(request.POST, request.FILES)
            if activity_form.is_valid():
                try:
                    activity_form.save()
                    messages.add_message(request, messages.INFO, "Activity was recorded!")
                except Exception as e:
                    messages.add_message(request, messages.ERROR, e)
    else:
        activity_form = CoworkingDayForm(initial={'visit_date': activity_date})

    # We can only waive days not associated with a bill
    has_activity = activity.count() > 0
    no_bills = activity.filter(line_item__isnull=False).count() == 0
    can_waive = has_activity and no_bills

    context = {'activity': activity,
               'activity_form': activity_form,
               'activity_date': activity_date,
               'can_waive': can_waive,
               'next_date': activity_date + timedelta(days=1),
               'previous_date': activity_date - timedelta(days=1)}
    return render(request, 'staff/activity/for_date.html', context)


@staff_member_required
def for_date(request, year, month, day):
    activity_date = date(year=int(year), month=int(month), day=int(day))
    return activity_for_date(request, activity_date)


@staff_member_required
def for_today(request):
    today = timezone.localtime(timezone.now())
    return HttpResponseRedirect(reverse('staff:activity:date', args=[], kwargs={'year': today.year, 'month': today.month, 'day': today.day}))


@staff_member_required
def for_user(request, username):
    user = get_object_or_404(User, username=username)
    date_range_form = DateRangeForm.from_request(request, days=30)
    start_date, end_date = date_range_form.get_dates()
    arp_logs = ArpLog.objects.for_user(username, start_date, end_date)
    door_logs = DoorEvent.objects.filter(user=user, timestamp__range=(start_date, end_date))
    daily_logs = CoworkingDay.objects.filter(user=user, visit_date__range=(start_date, end_date)).reverse()
    context = {'user': user,
               'date_range_form': date_range_form,
               'arp_logs': arp_logs,
               'door_logs': door_logs,
               'daily_logs': daily_logs}
    return render(request, 'staff/activity/for_user.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
