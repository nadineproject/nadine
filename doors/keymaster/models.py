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

import hid_control
from hid_control import DoorController
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

    def process_message(self, incoming_message):
        logger.debug("Incoming Message: '%s' " % incoming_message)
        
        outgoing_message = "No message"
        if incoming_message == Messages.TEST_QUESTION:
            outgoing_message = Messages.TEST_RESPONSE
        elif incoming_message == Messages.PULL_CONFIGURATION:
            outgoing_message = self.pull_config()
        elif incoming_message == Messages.PULL_DOOR_CODES:
            outgoing_message = self.pull_door_codes()
        elif incoming_message == Messages.FORCE_SYNC:
            outgoing_message = self.pull_door_codes(forceSync=True)
        elif incoming_message == Messages.MARK_SUCCESS:
            self.gatekeeper.mark_success()
            outgoing_message = Messages.SUCCESS_RESPONSE
        else:
            try:
                json_message = json.loads(incoming_message)
                print json_message
                # TODO save object
                outgoing_message = Messages.SUCCESS_RESPONSE
            except ValueError:
                pass
                
        
        logger.debug("Outgoing Message: '%s' " % outgoing_message)
        return outgoing_message

    def pull_config(self):
        doors = []
        for d in Door.objects.filter(keymaster=self):
            door = {'name':d.name, 'door_type':d.door_type, 'ip_address':d.ip_address, 'username':d.username, 'password':d.password}
            doors.append(door)
        return json.dumps(doors)

    def pull_door_codes(self, forceSync=False):
        if not forceSync:
            if self.sync_ts:
                if DoorCode.objects.filter(modified_ts__gt=self.sync_ts).count() == 0:
                    # Nothing to do here
                    return []
        # Pull all the codes and send them back
        codes = []
        for c in DoorCode.objects.all():
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)

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
    
    def __str__(self): 
        return "%s: %s" % (self.keymaster.description, self.name)


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
    code = models.CharField(max_length=16)
    event_type = models.CharField(max_length=1, choices=DoorEventTypes.CHOICES, default=DoorEventTypes.UNKNOWN, null=False)
    event_description = models.CharField(max_length=256)
    