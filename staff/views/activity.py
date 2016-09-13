import time as timeo
from datetime import date, datetime, timedelta


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


from doors.keymaster.models import DoorEvent
from arpwatch.models import ArpLog
from staff.forms import DailyLogForm, DateRangeForm
from nadine.models import DailyLog, Membership

START_DATE_PARAM = 'start'
END_DATE_PARAM = 'end'

def date_range_from_request(request, days=31):
    # Pull the Start Date param
    start = request.POST.get(START_DATE_PARAM, None)
    if not start:
        start = request.GET.get(START_DATE_PARAM, None)
    if not start:
        start_date = timezone.now().date() - timedelta(days=days)
        start = start_date.isoformat()
    end = request.POST.get(END_DATE_PARAM, None)
    if not end:
        end = request.GET.get(END_DATE_PARAM, None)
    if not end:
        tomorrow = timezone.now() + timedelta(days=1)
        end = tomorrow.date().isoformat()

    return (start, end)


@staff_member_required
def activity(request):
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    starteo = timeo.strptime(start, "%Y-%m-%d")
    start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
    endeo = timeo.strptime(end, "%Y-%m-%d")
    end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
    days = [{'date': start_date + timedelta(days=i)} for i in range((end_date - start_date).days)]
    days.reverse()
    for day in days:
        memberships = Membership.objects.active_memberships(day['date'])
        day['daily_logs'] = DailyLog.objects.filter(visit_date=day['date']).count()
        day['has_desk'] = memberships.filter(has_desk=True).count()
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
    return render_to_response('staff/activity.html', {'days': days, 'graph_size': graph_size, 'max_has_desk': max_has_desk, 'max_membership': max_membership, 'max_daily_logs': max_daily_logs, 'max_total': max_total, 'total_daily_logs': total_daily_logs, 'date_range_form': date_range_form, 'start': start, 'end': end}, context_instance=RequestContext(request))


@staff_member_required
def list(request):
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    starteo = timeo.strptime(start, "%Y-%m-%d")
    start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
    endeo = timeo.strptime(end, "%Y-%m-%d")
    end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
    daily_logs = DailyLog.objects.filter(visit_date__range=(start_date, end_date))
    return render_to_response('staff/activity_list.html', {'daily_logs': daily_logs, 'date_range_form': date_range_form, 'start_date': start_date, 'end_date': end_date}, context_instance=RequestContext(request))


@staff_member_required
def activity_for_date(request, activity_date):
    daily_logs = DailyLog.objects.filter(visit_date=activity_date).reverse()

    if request.method == 'POST':
        daily_log_form = DailyLogForm(request.POST, request.FILES)
        if daily_log_form.is_valid():
            try:
                daily_log_form.save()
                messages.add_message(request, messages.INFO, "Activity was recorded!")
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
    else:
        daily_log_form = DailyLogForm(initial={'visit_date': activity_date})

    return render_to_response('staff/activity_date.html', {'daily_logs': daily_logs, 'daily_log_form': daily_log_form, 'activity_date': activity_date, 'next_date': activity_date + timedelta(days=1), 'previous_date': activity_date - timedelta(days=1), }, context_instance=RequestContext(request))


@staff_member_required
def for_date(request, year, month, day):
    activity_date = date(year=int(year), month=int(month), day=int(day))
    return activity_for_date(request, activity_date)


@staff_member_required
def for_today(request):
    today = timezone.localtime(timezone.now())
    return HttpResponseRedirect(reverse('staff_activity_day', args=[], kwargs={'year': today.year, 'month': today.month, 'day': today.day}))


@staff_member_required
def for_user(request, username):
    user = get_object_or_404(User, username=username)

    tz = timezone.get_current_timezone()
    start, end = date_range_from_request(request, days=10)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    start_date = timezone.make_aware(datetime.strptime(start, "%Y-%m-%d"), tz)
    end_date = timezone.make_aware(datetime.strptime(end, "%Y-%m-%d"), tz)

    arp_logs = ArpLog.objects.for_user(username, start_date, end_date)
    door_logs = DoorEvent.objects.filter(user=user, timestamp__range=(start_date, end_date))
    daily_logs = DailyLog.objects.filter(user=user, visit_date__range=(start_date, end_date)).reverse()

    return render_to_response('staff/activity_user.html', {'user':user, 'date_range_form': date_range_form,
        'arp_logs':arp_logs, 'door_logs':door_logs, 'daily_logs':daily_logs}, context_instance=RequestContext(request))
