import json
import logging
import requests

from datetime import datetime, time, date, timedelta

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone

from doors.core import DoorTypes, DoorEventTypes, Messages, EncryptedConnection

logger = logging.getLogger(__name__)


class KeymasterManager(models.Manager):

    # Pull an object from the database linked by the incoming IP address
    def by_ip(self, ip_address):
        try:
            keymaster = self.get(gatekeeper_ip=ip_address)
            if not keymaster.is_enabled:
                raise Exception("Keymaster for this IP address is disabled")
            # A save updates the access_ts
            keymaster.save()
            return keymaster
        except MultipleObjectsReturned as me:
            logger.error("Multiple Keymasters returned for IP: %s" % ip_address)
        except ObjectDoesNotExist as de:
            # The first time we see a message from a given IP we create a disabled keymaster
            self.create(gatekeeper_ip=ip_address, description="New Keymaster", is_enabled=False)
        return None


class Keymaster(models.Model):
    objects = KeymasterManager()

    description = models.CharField(max_length=64)
    gatekeeper_ip = models.GenericIPAddressField(blank=False, null=False, unique=True)
    encryption_key = models.CharField(max_length=128)
    access_ts = models.DateTimeField(auto_now=True)
    sync_ts = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)

    def get_encrypted_connection(self):
        return EncryptedConnection(self.encryption_key)

    def pull_config(self):
        doors = []
        for d in Door.objects.filter(keymaster=self):
            door = {'name':d.name, 'door_type':d.door_type, 'ip_address':d.ip_address, 'username':d.username, 'password':d.password}
            door['last_event_ts'] = d.get_last_event_ts()
            doors.append(door)
        return json.dumps(doors)

    def check_door_codes(self):
        # Return True if there are new codes since the last sync
        if not self.sync_ts or DoorCode.objects.filter(modified_ts__gt=self.sync_ts).count() > 0:
            return Messages.NEW_DATA
        return Messages.NO_NEW_DATA

    def pull_door_codes(self):
        # Pull all the codes and send them back
        codes = []
        for c in DoorCode.objects.all():
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)

    def process_event_logs(self, event_logs):
        if not event_logs:
            raise Exception("process_event_logs: No event logs to process!")
        logger.debug("process_event_logs: %d logs to process" % len(event_logs))

        for door_name, events_to_process in event_logs.items():
            door = Door.objects.get(name=door_name)
            last_ts = door.get_last_event_ts()
            for event in events_to_process:
                timestamp = event['timestamp']
                if timestamp == last_ts:
                    # We have caught up with the logs so we can stop now
                    break
                
                description = event['description']
                event_type = event['door_event_type']
                door_code = event.get('rawCardNumber', None)
                user = None
                if door_code:
                    c = DoorCode.objects.filter(code=door_code).first()
                    if c:
                        user = c.user
                DoorEvent.objects.create(timestamp=timestamp, door=door, user=user, code=door_code, event_type=event_type, event_description=description)
        
        return Messages.SUCCESS_RESPONSE

    def mark_success(self):
        self.sync_ts = timezone.now()
        self.save()

    def force_sync(self):
        self.sync_ts = None
        self.save()

    def __str__(self): 
        return self.description


class Door(models.Model):
    name = models.CharField(max_length=16, unique=True)
    door_type = models.CharField(max_length=16, choices=DoorTypes.CHOICES)
    keymaster = models.ForeignKey(Keymaster)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    ip_address = models.GenericIPAddressField()
    
    def get_last_event(self):
        return DoorEvent.objects.filter(door=self).order_by('timestamp').reverse().first()
    
    def get_last_event_ts(self):
        # Convert the last event timestamp to the format we get from the doors
        ts = None
        last_event = self.get_last_event()
        if last_event and last_event.timestamp:
            tz = timezone.get_current_timezone()
            ts = str(last_event.timestamp.astimezone(tz))[:19].replace(" ", "T")
        return ts
    
    def __str__(self): 
        return self.name


class DoorCode(models.Model):
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True)

    def __str__(self): 
        return '%s: %s' % (self.user, self.code)


class DoorEvent(models.Model):
    timestamp = models.DateTimeField(null=False)
    door = models.ForeignKey(Door, null=False)
    user = models.ForeignKey(User, null=True, db_index=True)
    code = models.CharField(max_length=16, null=True)
    event_type = models.CharField(max_length=1, choices=DoorEventTypes.CHOICES, default=DoorEventTypes.UNKNOWN, null=False)
    event_description = models.CharField(max_length=256)
    
    def __str__(self): 
        return '%s: %s' % (self.door, self.event_description)
    
    