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
    SEND_NEW_DATA = "send_new_data"

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
    
    ip_address = models.GenericIPAddressField(blank=False, null=False, unique=True)
    encryption_key = models.CharField(max_length=128)
    access_ts = models.DateTimeField(auto_now=True)
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
        elif incoming_message == Messages.SEND_NEW_DATA:
            outgoing_message = self.send_new_data()
        
        return self.encrypt_message(outgoing_message)
    
    def pull_config(self):
        doors = []
        for d in Door.objects.filter(gatekeeper=self):
            door = {'name': d.name, 'ip_address':d.ip_address, 'username': d.username, 'password': d.password}
            doors.append(door)
        return json.dumps(doors)

    def send_new_data(self):
        return "no new data"

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
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    door = models.ForeignKey(Door)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True, db_index=True)
    start = models.DateTimeField(null=False)
    end = models.DateTimeField(null=True, blank=True)
    sync_ts = models.DateTimeField(blank=True, null=True)

    def is_synced(self):
        return sync_ts != None

    def __str__(self): 
        return '%s - %s: %s' % (self.user, self.door, self.code)
