import json
import logging

from datetime import datetime, time, date, timedelta

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    PULL_CONFIGURATION = "pull_configuration"
    PULL_DOOR_CODES = "pull_door_codes"
    MARK_SUCCESS = "mark_success"
    SUCCESS_RESPONSE = "OK"

class GatekeeperManager(models.Manager):
    
    def by_ip(self, ip):
        try:
            gatekeeper = self.get(ip_address=ip)
            if not gatekeeper.is_enabled:
                raise Exception("Gatekeeper for this IP address is disabled")
            # A save updates the access_ts
            gatekeeper.save()
            return gatekeeper
        except MultipleObjectsReturned as me:
            logger.error("Multiple Gatekeepers returned for IP: %s" % ip)
        except ObjectDoesNotExist as de:
            # The first time we see a message from a given IP we create a disabled gatekeeper
            self.create(ip_address=ip, is_enabled=False)
            
        return None

class Gatekeeper(models.Model):
    objects = GatekeeperManager()
    
    description = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(blank=False, null=False, unique=True)
    encryption_key = models.CharField(max_length=128)
    access_ts = models.DateTimeField(auto_now=True)
    success_ts = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)

    def decrypt_message(self, message):
        if not self.encryption_key:
            raise Exception("No encryption key")
        f = Fernet(bytes(self.encryption_key))
        ten_minutes = 10 * 60
        return f.decrypt(bytes(message), ttl=ten_minutes)

    def encrypt_message(self, message):
        if not self.encryption_key:
            raise Exception("No encryption key")
        f = Fernet(bytes(self.encryption_key))
        return f.encrypt(bytes(message))
    
    def process_message(self, message):
        incoming_message = self.decrypt_message(message)

        outgoing_message = "No message"
        if incoming_message == Messages.TEST_QUESTION:
            outgoing_message = Messages.TEST_RESPONSE
        elif incoming_message == Messages.PULL_CONFIGURATION:
            outgoing_message = self.pull_config()
        elif incoming_message == Messages.PULL_DOOR_CODES:
            outgoing_message = self.pull_door_codes()
        elif incoming_message == Messages.MARK_SUCCESS:
            outgoing_message = self.mark_success()
        
        return self.encrypt_message(outgoing_message)
    
    def pull_config(self):
        doors = []
        for d in Door.objects.filter(gatekeeper=self):
            door = {'name':d.name, 'ip_address':d.ip_address, 'username':d.username, 'password':d.password}
            doors.append(door)
        return json.dumps(doors)

    def pull_door_codes(self):
        new_codes = DoorCode.objects.filter(modified_ts__gt=self.success_ts)
        if not new_codes:
            return "{}"
            
        codes = []
        for c in DoorCode.objects.all():
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)

    def mark_success(self):
        self.success_ts = timezone.now()
        self.save()
        return SUCCESS_RESPONSE

    def __str__(self): 
        return self.ip_address

class Door(models.Model):
    name = models.CharField(max_length=16, unique=True)
    gatekeeper = models.ForeignKey(Gatekeeper)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    ip_address = models.GenericIPAddressField()

    def __str__(self): 
        return self.name

class DoorCode(models.Model):
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True)

    def __str__(self): 
        return '%s - %s: %s' % (self.user, self.door, self.code)
