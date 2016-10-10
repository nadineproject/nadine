import os, uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User

from PIL import Image
import logging

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

    def available(self, start, end, has_av=None, has_phone=None, floor=None, seats=None):

        rooms = self.all()
        if has_av != None:
            rooms = rooms.filter(has_av=has_av)
        if has_phone != None:
            rooms = rooms.filter(has_phone=has_phone)
        if floor != None:
            rooms = rooms.filter(floor=floor)
        if seats != None:
            rooms = rooms.filter(seats__gte=seats)

        straddling = Q(event__start_ts__lte=start, event__end_ts__gt=start)
        sandwich = Q(event__start_ts__gte=start, event__start_ts__lt=end)
        overlap = Q(event__start_ts__lte=start, event__end_ts__gte=end)
        rooms = rooms.exclude(straddling| sandwich | overlap)

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

    def __unicode__(self):
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

    def get_calendar(self, start, end, target_date, end_date):
        calendar = self.get_raw_calendar()
        search_start = start.replace(':', '')
        search_end = end.replace(':', '')
        events = self.event_set.filter(room=self, start_ts__gte=target_date, end_ts__lte=end_date)
        print

        for event in events:
            start_wtz = timezone.make_naive(event.start_ts, timezone.get_current_timezone())
            end_wtz = timezone.make_naive(event.end_ts, timezone.get_current_timezone())
            starts = start_wtz.strftime('%H%M')
            ends = end_wtz.strftime('%H%M')
            for block in calendar:
                id = block['mil_hour'] + block['minutes']
                if int(starts) <= int(id) and int(id) <= int(ends):
                    block['status'] = 'reserved'
                else:
                    block['status'] = 'available'

        for block in calendar:
            id = block['mil_hour'] + block['minutes']
            if int(search_start) <= int(id) and int(id) <= int(search_end):
                block['status'] = 'searched'

        return calendar
