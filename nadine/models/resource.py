from __future__ import unicode_literals

import os, uuid
import importlib
from datetime import datetime, timedelta, date
from abc import ABCMeta, abstractmethod

from django.db import models
from django.conf import settings
from django.db.models import Q, F
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now, get_current_timezone

from PIL import Image
import logging

from nadine.models.usage import Event

logger = logging.getLogger(__name__)


def room_img_upload_to(instance, filename):
    # rename file to a unique string
    ext = filename.split('.')[-1]
    filename = "%s_%s.%s" % (instance.name, uuid.uuid4(), ext.lower())

    upload_path = "rooms/"
    upload_abs_path = os.path.join(settings.MEDIA_ROOT, upload_path)
    if not os.path.exists(upload_abs_path):
        os.makedirs(upload_abs_path)
    return os.path.join(upload_path, filename)


class RoomManager(models.Manager):

    def available(self, start=None, end=None, has_av=None, has_phone=None, floor=None, seats=None):
        # Default time is now, for one hour
        if not start:
            start = localtime(now())
        if not end:
            end = start + timedelta(hours=1)

        rooms = self.all()

        if has_av != None:
            rooms = rooms.filter(has_av=has_av)
        if has_phone != None:
            rooms = rooms.filter(has_phone=has_phone)
        if floor != None:
            rooms = rooms.filter(floor=floor)
        if seats != None:
            rooms = rooms.filter(seats__gte=seats)

        events = Event.objects.all()
        for event in events:
            if event.start_ts >= start and event.start_ts < end:
                rooms = rooms.exclude(name=event.room)
            elif (event.start_ts <= start) and (event.end_ts > start):
                rooms = rooms.exclude(name=event.room)
            elif (event.start_ts < end) and (event.end_ts > start):
                rooms = rooms.exclude(name=event.room)

        # This code looks cleaner but running into bugs currently
        # head = Q(event__start_ts__gte=start, event__start_ts__lt=end)
        # middle = Q(event__start_ts__lte=start, event__end_ts__gt=start)
        # tail = Q(event__start_ts__lt=end, event__end_ts__gt=start)
        #
        # rooms = rooms.exclude(head | middle | tail)

        return rooms


class Room(models.Model):
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=128, null=True)
    description = models.TextField(blank=True, null=True)
    floor = models.SmallIntegerField()
    seats = models.SmallIntegerField()
    max_capacity = models.SmallIntegerField()
    has_av = models.BooleanField(default=False)
    has_phone = models.BooleanField(default=False)
    default_rate = models.DecimalField(decimal_places=2, max_digits=9)
    #image = models.ImageField(upload_to=room_img_upload_to, blank=True, null=True, help_text="Images should be 500px x 325px or a 1 to 0.65 ratio ")
    image = models.ImageField(upload_to=room_img_upload_to, blank=True, null=True)

    objects = RoomManager()

    def __str__(self):
        return self.name

    def get_events(self, start, end):
        return self.event_set.filter(start_ts__gte=start, end_ts__lte=end)

    def get_raw_calendar(self):
        # Calendar is a list of {hour, minute} time blocks
        calendar = []

        # Default OPEN_TIME is 8AM
        open_hour = '8'
        open_minute = '00'
        if hasattr(settings, 'OPEN_TIME') and ':' in settings.OPEN_TIME:
            open_hour = settings.OPEN_TIME.split(':')[0]
            open_minute = settings.OPEN_TIME.split(':')[1]

        # Default CLOSE_TIME is 6PM
        close_hour = '18'
        close_minute = '00'
        if hasattr(settings, 'CLOSE_TIME') and ':' in settings.CLOSE_TIME:
            close_hour = settings.CLOSE_TIME.split(':')[0]
            close_minute = settings.CLOSE_TIME.split(':')[1]

        for num in range(int(open_hour), int(close_hour)):
            minutes = open_minute
            for count in range(0, 4):
                time_block = {}
                calendar.append(time_block)
                if num <= 12:
                    time_block['hour'] = str(num)
                else:
                    time_block['hour'] = str(num - 12)
                time_block['mil_hour'] = str(num)

                time_block['minutes'] = minutes
                if minutes == '00':
                    minutes = '15'
                elif minutes =='15':
                    minutes = '30'
                elif minutes =='30':
                    minutes = '45'
                else:
                    minutes = '00'
                    num += 1
        return calendar

    def get_calendar(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()

        # Start with the raw calendar
        calendar = self.get_raw_calendar()

        # Extract the start and end times from our target date and the raw calendar
        first_block = calendar[0]
        last_block = calendar[len(calendar) - 1]
        tz = get_current_timezone()
        start = datetime(year=target_date.year, month=target_date.month, day=target_date.day, hour=int(first_block['mil_hour']), minute=int(first_block['minutes']), tzinfo=tz)
        end = datetime(year=target_date.year, month=target_date.month, day=target_date.day, hour=int(last_block['mil_hour']), minute=int(last_block['minutes']), tzinfo=tz)
        end = end + timedelta(minutes=15)
        # print("Start: %s, End: %s, TZ: %s" % (start, end, tz))

        # Loop through the events for this day and mark which blocks are reserved
        # We use time integers in the form of HOURMIN (830, 1600, etc) for comparison
        events = self.event_set.filter(room=self, start_ts__gte=start, end_ts__lte=end)
        for event in events:
            start_int = int(localtime(event.start_ts).strftime('%H%M'))
            end_int = int(localtime(event.end_ts).strftime('%H%M'))
            for block in calendar:
                block_int = int(block['mil_hour'] + block['minutes'])
                #print ("%d, %d, %d" % (start_int, end_int, block_int))
                if start_int <= block_int and block_int < end_int:
                    #print "Reserved!"
                    block['reserved'] = True

        return calendar


class ResourceManager(models.Manager):

    def resource_by_key(self, key):
        # print("pulling '%s' resource" % key)
        resource_search = Resource.objects.filter(key=key)
        if resource_search.count() == 0:
            raise Exception("Could not find '%s' resource" % key)
        if resource_search.count() > 1:
            raise Exception("Multiple '%s' resources found" % key)
        return resource_search.first()

    @property
    def day_resource(self):
        return self.resource_by_key(Resource.DAY_KEY)

    @property
    def key_resource(self):
        return self.resource_by_key(Resource.KEY_KEY)

    @property
    def mail_resource(self):
        return self.resource_by_key(Resource.MAIL_KEY)

    @property
    def desk_resource(self):
        return self.resource_by_key(Resource.DESK_KEY)

    @property
    def room_resource(self):
        return self.resource_by_key(Resource.ROOM_KEY)


class Resource(models.Model):
    DAY_KEY = "day"
    KEY_KEY = "key"
    MAIL_KEY = "mail"
    DESK_KEY = "desk"
    ROOM_KEY = "room"

    name = models.CharField(max_length=64, unique=True)
    key = models.CharField(max_length=8, unique=True, null=True, blank=True)
    default_rate = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    tracker_class = models.CharField(max_length=64, null=True, blank=True)

    objects = ResourceManager()

    def __str__(self):
        return self.name

    def is_trackable(self):
        return self.tracker_class is not None

    def get_tracker(self):
        if not self.tracker_class:
            return None

        try:
            mod_index = self.tracker_class.rfind(".")
            module_name = self.tracker_class[0:mod_index]
            class_name = self.tracker_class[mod_index+1:]
            logger.debug("Loading Class:  module_name='%s', class_name='%s'" % (module_name, class_name))
            m = importlib.import_module(module_name)
            loaded_class = getattr(m, class_name)
            instance = loaded_class(self)
            if not isinstance(instance, ResourceTrackerABC):
                raise Exception("Tracker class not an instance of ResourceTrackerABC")
            return instance
        except Exception as e:
            raise Exception("Could not load tracker class", e)

    def save(self, *args, **kwargs):
        # Try and get a tracker of this class and raise an Exception if it's invalid
        self.get_tracker()
        super(Resource, self).save(*args, **kwargs)


################################################################################
# Resource Trackers
################################################################################


class ResourceTrackerABC:
    __metaclass__ = ABCMeta

    def __init__(self, resource):
        self.resource = resource

    @abstractmethod
    def get_activity(self, user, period_start, period_end):
        # Return a list of line items for all activity in the given time period
        pass


class CoworkingDayTracker(ResourceTrackerABC):

    def get_activity(self, user, period_start, period_end):
        from nadine.models.usage import CoworkingDay
        from nadine.models.billing import BillLineItem
        logger.debug("get_activity(user=%s, period_start=%s, period_end=%s)" % (user, period_start, period_end))
        day_resource = Resource.objects.day_resource
        billed_coworking_days = BillLineItem.objects.filter(resource=day_resource).values('activity_id')
        query = CoworkingDay.objects.filter(user=user, visit_date__range=(period_start, period_end), payment='Bill').exclude(id__in=billed_coworking_days)
        return query.annotate(activity_date=F('visit_date'))


class RoomBookingTracker(ResourceTrackerABC):

    def get_activity(self, user, period_start, period_end):
        # TODO - complete
        return []


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
