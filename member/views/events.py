import time
import traceback
import decimal
from datetime import date, datetime, timedelta
from calendar import Calendar, HTMLCalendar

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.timezone import localtime, now


from nadine.models.usage import CoworkingDay, Event
from nadine.models.resource import Room
from nadine.forms import EventForm
# from nadine.settings import MEMBER_DISCOUNT

from member.views.core import is_active_member


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def events_google(request, location_slug=None):
    return render(request, 'member/events/events_google.html', {'settings': settings})


def quarter_hours(hour, minutes):
    if len(hour) < 2:
        hour = '0' + hour

    if int(minutes) < 15:
        minutes = '00'
    elif int(minutes) < 30:
        minutes = '15'
    elif int(minutes) < 45:
        minutes = '30'
    elif int(minutes) < 59:
        minutes = '45'
    else:
        minutes = '00'
        hour = int(mil_start[1] + 1)

    return hour, minutes


def coerce_times(start, end, date):
    if len(start) > 5:
        start = start.split(" ")
        if start[1] == 'PM':
            mil_start = start[0].split(":")
            if int(mil_start[0]) < 12:
                hour = int(mil_start[0]) + 12
            else:
                hour = mil_start[0]
            start_hour, start_minutes = quarter_hours(str(hour), mil_start[1])
            start = str(hour) + ':' + mil_start[1]
        else:
            mil_start = start[0].split(":")
            start_hour, start_minutes = quarter_hours(mil_start[0], mil_start[1])
            start = str(start_hour) + ':' + start_minutes
    else:
        mil_start = start.split(":")
        start_hour, start_minutes = quarter_hours(mil_start[0], mil_start[1])
        start = str(start_hour) + ':' + start_minutes
    if len(end) > 5:
        end = end.split(" ")
        if end[1] == 'PM':
            mil_end = end[0].split(":")
            if int(mil_end[0]) < 12:
                hour = int(mil_end[0]) + 12
            else:
                hour = mil_end[0]
            end_hour, end_minutes = quarter_hours(str(hour), mil_end[1])
            end = str(end_hour) + ':' + end_minutes
        else:
            mil_end = end[0].split(":")
            end_hour, end_minutes = quarter_hours(mil_end[0], mil_end[1])
            end = str(end_hour) + ':' + end_minutes
    else:
        mil_end = end.split(":")
        end_hour, end_minutes = quarter_hours(mil_end[0], mil_end[1])
        end = str(end_hour) + ':' + end_minutes

    start_dt = datetime.strptime(date + " " + start, "%Y-%m-%d %H:%M")
    start_ts = timezone.make_aware(start_dt, timezone.get_current_timezone())
    end_dt = datetime.strptime(date + " " + end, "%Y-%m-%d %H:%M")
    end_ts = timezone.make_aware(end_dt, timezone.get_current_timezone())

    return start_ts, end_ts, start, end


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def create_booking(request, username):
    user = get_object_or_404(User, username=username)
    # Process URL variables
    has_av = request.GET.get('has_av', None)
    has_phone = request.GET.get('has_phone', None)
    floor = request.GET.get('floor', None)
    seats = request.GET.get('seats', None)
    date = request.GET.get('date', str(timezone.now().date()))
    start = request.GET.get('start', str(datetime.now().hour) + ':' + str(datetime.now().minute))
    end = request.GET.get('end', str(datetime.now().hour + 2) + ':' + str(datetime.now().minute))
    all_day = request.GET.get('all_day', None)
    members_only = request.GET.get('members_only', None)

    floors = Room.objects.filter().values('floor').distinct().order_by('floor')

    if all_day:
        start = settings.OPEN_TIME
        end = settings.CLOSE_TIME

    # Turn our date, start, and end strings into timestamps
    start_ts, end_ts, start, end = coerce_times(start, end, date)

    start_ts_mil = ((time.mktime(start_ts.timetuple()) * 1000))

    # Make auto date for start and end if not otherwise given
    room_dict = {}
    rooms = Room.objects.available(start=start_ts, end=end_ts, has_av=has_av, has_phone=has_phone, floor=floor, seats=seats)

    ''' Return all rooms if member and limited rooms if not '''
    # To be implemented once model changed
    # if user.membership.active_subscriptions():
    #     rooms = Room.objects.available(start=start_ts, end=end_ts, has_av=has_av, has_phone=has_phone, floor=floor, seats=seats, members_only=members_only)
    #     # if room is billable, add a rate to the room
    #     for room in rooms:
    #         if room.members_only == False:
    #             for room in rooms:
    #                 room.rate = format((MEMBER_DISCOUNT * room.default_rate), '.2f')
    #             room.rate =  * room.default_rate
    # else:
    #     rooms = Room.objects.available(start=start_ts, end=end_ts, has_av=has_av, has_phone=has_phone, floor=floor, seats=seats).filter(members_only=False)
    #     for r in rooms:
    #         r.rate = r.default_rate

    # Get all the events for each room in that day
    target_date = start_ts.date()

    for room in rooms:
        calendar = room.get_calendar(target_date)
        room_dict[room] = calendar
        if len(calendar) > 48:
            loop_count = 4
        else:
            loop_count = 2

        # Infuse calendar with search range
        search_start = start.replace(':', '')
        search_end = end.replace(':', '')

        for block in calendar:
            id = block['mil_hour'] + block['minutes']
            if int(search_start) <= int(id) and int(id) <= int(search_end):
                block['searched'] = True

    if request.method == 'POST':
        room = request.POST.get('room')
        start = request.POST.get('start')
        end = request.POST.get('end')
        date = request.POST.get('date')
        rate = request.POST.get('rate', None)

        return HttpResponseRedirect(reverse('member:event:confirm_booking', kwargs={'room': room, 'start': start, 'end': end, 'date': date, 'rate': rate}))

    context = {'rooms': rooms,
               'start': start,
               'end': end,
               'date': date,
               'has_av': has_av,
               'floor': floor,
               'floors': floors,
               'seats': seats,
               'all_day': all_day,
               'loop_count': loop_count,
               'has_phone': has_phone,
               'members_only': members_only,
               'room_dict': room_dict,
               'start_ts_mil': start_ts_mil,
               'user': user,
               }
    return render(request, 'member/events/booking_create.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def confirm_booking(request, room, start, end, date, rate):
    user = request.user
    room = get_object_or_404(Room, name=room)

    start_ts, end_ts, start, end = coerce_times(start, end, date)
    target_date = start_ts.date()

    event_dict = {}
    calendar = room.get_calendar(target_date)
    event_dict[room] = calendar
    if len(calendar) > 48:
        loop_count = 4
    else:
        loop_count = 2

    # Infuse room calendar with search range
    search_start = start.replace(':', '')
    search_end = end.replace(':', '')

    for block in calendar:
        block_int = int(block['mil_hour'] + block['minutes'])
        if int(search_start) <= block_int and block_int <= int(search_end):
            block['searched'] = True

    if request.method == 'POST':
        booking_form = EventForm(request.POST)
        user = request.user
        room = request.POST.get('room')
        room = get_object_or_404(Room, name=room)
        start = request.POST.get('start')
        end = request.POST.get('end')
        date = request.POST.get('date')
        start_ts, end_ts, start, end = coerce_times(start, end, date)
        description = request.POST.get('description', '')
        charge = request.POST.get('charge', 0)
        is_public = request.POST.get('is_public', False)
        if is_public == 'True':
            is_public = True
        else:
            is_public = False
        event = Event(user=user, room=room, start_ts=start_ts, end_ts=end_ts, description=description, charge=charge, is_public=is_public)

        stillAv = Room.objects.available(start=start_ts, end=end_ts)

        if room in stillAv:
            try:
                event.save()

                return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))

            except Exception as e:
                messages.error(request, str(e))
                logger.error(str(e))
        else:
            messages.error(request, 'This room is no longer available at the requested time.')
    else:
        booking_form = EventForm()

    context = {'booking_form': booking_form,
               'start': start,
               'end': end,
               'room': room,
               'date': date,
               'rate': rate,
               'loop_count': loop_count,
               'event_dict': event_dict,
               }
    return render(request, 'member/events/booking_confirm.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def calendar(request):
    events = Event.objects.filter(is_public=True)
    data = []

    for event in events:
        host = get_object_or_404(User, id=event.user_id)
        data.append((event, host))

    if request.method == 'POST':
        user = request.user
        start = request.POST.get('start')
        end = request.POST.get('end')
        date = request.POST.get('date')

        start_ts, end_ts, start, end = coerce_times(start, end, date)
        if start_ts < end_ts:
            description = request.POST.get('description', '')
            charge = request.POST.get('charge', 0)
            is_public = True

            event = Event(user=user, start_ts=start_ts, end_ts=end_ts, description=description, charge=charge, is_public=is_public)
            event.save()

            return HttpResponseRedirect(reverse('member:event:calendar'))
        else:
            messages.add_message(request, messages.ERROR, "Did not save your event. Double check that the event start is before the end time. Thank you.")

    template = 'member/events/calendar.html'
    context = {'data': data, 'CALENDAR_DICT': settings.CALENDAR_DICT}
    if hasattr(settings, 'GOOGLE_CALENDAR_ID'):
        context['feed_url'] = "https://calendar.google.com/calendar/ical/%s/public/basic.ics" % settings.GOOGLE_CALENDAR_ID
        context['GOOGLE_CALENDAR_ID'] = settings.GOOGLE_CALENDAR_ID
        context['GOOGLE_API_KEY'] = settings.GOOGLE_API_KEY
        template = 'member/events/calendar_google.html'
    return render(request, template, context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
