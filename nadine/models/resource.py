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
        sandwich = Q(event__start_ts__gte=start, event__start_ts__lte=end)
        overlap = Q(event__start_ts__lte=start, event__end_ts__gte=end)
        rooms = rooms.exclude(straddling| sandwich | overlap)
        return rooms

    def reservations(self, room_dict, ids):
        res_dict = {}
        for room, events in room_dict.items():
            if events:
                for event in events:
                    start_wtz = timezone.make_naive(event.start_ts, timezone.get_current_timezone())
                    end_wtz = timezone.make_naive(event.end_ts, timezone.get_current_timezone())
                    starts = start_wtz.strftime('%H%M')
                    ends = end_wtz.strftime('%H%M')
                    reserved = []
                    if room not in res_dict.keys():
                        for id in ids:
                            if int(starts) <= int(id) and int(id) <= int(ends):
                                reserved.append(id)
                        res_dict[room] = reserved
                    else:
                        for id in ids:
                            if int(starts) <= int(id) and int(id) <= int(ends):
                                res_dict[room].append(id)
            else:
                res_dict[room] = {}
        return res_dict

    def searched(self, start, end, ids):
        search_block = []
        for id in ids:
            if int(start.replace(':', '')) <= int(id) and int(id) <= int(end.replace(':', '')):
                search_block.append(id)
        return search_block


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
