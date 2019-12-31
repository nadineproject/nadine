from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


class MOTDManager(models.Manager):

    def for_date(self, day=None):
        if not day:
            day = timezone.now()
        return MOTD.objects.filter(start_ts__lte=day, end_ts__gte=day).first()

    def for_today(self):
        today = timezone.now()
        motd = self.for_date(today)
        if not motd:
            message = settings.MOTD
            if not message:
                message = "Welcome!"
            delay = settings.MOTD_TIMEOUT
            if not delay:
                delay=10000
            motd = MOTD(start_ts=today, end_ts=today, message=message, delay_ms=delay)
        return motd


class MOTD(models.Model):
    objects = MOTDManager()

    start_ts = models.DateTimeField(null=False, blank=False)
    end_ts = models.DateTimeField(null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    delay_ms = models.SmallIntegerField(null=False, blank=False, default=5000)

    def __str__(self):
        return self.message


class HelpText(models.Model):
    title = models.CharField(max_length=128)
    template = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=16, unique=True)
    order = models.SmallIntegerField()

    def __str__(self): return self.title


class UserNotification(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    notify_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notify", blank=False, on_delete=models.CASCADE)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="target", blank=False, on_delete=models.CASCADE)
    sent_date = models.DateTimeField(blank=True, null=True, default=None)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
