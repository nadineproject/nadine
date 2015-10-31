from datetime import datetime, time, date, timedelta

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User

class Gatekeeper(models.Model):
    ip_address = models.GenericIPAddressField(blank=False, null=False, unique=True)
    encryption_key = models.CharField(max_length=128)
    sync_ts = models.DateTimeField(blank=True, null=True)

    def __str__(self): 
        return self.description

class HIDDoor(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=128)
    stub = models.CharField(max_length=16)
    def __str__(self): 
        return self.description

class DoorCode(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    door = models.ForeignKey(HIDDoor)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True, db_index=True)
    start = models.DateTimeField(null=False)
    end = models.DateTimeField(null=True, blank=True)
    sync_ts = models.DateTimeField(blank=True, null=True)

    def is_synced(self):
        return sync_ts != None

    def __str__(self): 
        return '%s - %s: %s' % (self.user, self.door, self.code)
