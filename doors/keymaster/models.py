import json
import logging
import requests

from datetime import datetime, time, date, timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core import mail
from django.utils.timezone import localtime, now, make_aware, get_current_timezone

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
    success_ts = models.DateTimeField(null=True, blank=True)
    sync_ts = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)
    is_syncing = models.BooleanField(default=False)

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
        # Mark that we are syncing so humans know something is going on
        self.is_syncing = True
        self.save()

        # Pull all the codes and send them back
        codes = []
        for c in DoorCode.objects.all().order_by('user__username'):
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)

    def process_event_logs(self, event_logs):
        if not event_logs:
            raise Exception("process_event_logs: No event logs to process!")
        #logger.debug("process_event_logs: %d doors to process" % len(event_logs))

        for door_name, events_to_process in list(event_logs.items()):
            door = Door.objects.get(name=door_name)
            last_ts = door.get_last_event_ts()
            logger.debug("Processing events for '%s'. Last TS = %s" % (door_name, last_ts))
            for event in events_to_process:
                #print("New Event: %s" % event)
                timestamp = event['timestamp']
                if timestamp == last_ts:
                    # We have caught up with the logs so we can stop now
                    break
                    # TODO - If we dont' reach this point ever we should signal to the
                    # Gatekeeper that we needed more logs.

                # Convert the timestamp string to a datetime object
                # Assert the timezone is the local timezone for this timestamp
                tz = get_current_timezone()
                naive_timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                tz_timestamp = tz.localize(naive_timestamp)

                # TODO - If our timestamp is too far in the future we have a time sync problem.

                description = event.get('description')
                event_type = event.get('door_event_type')
                door_code = event.get('cardNumber')

                # Extract the User from a given username or the door code if we have it
                user = None
                cardholder = event.get('cardHolder')
                if cardholder:
                    username = cardholder.get('username')
                    if username:
                        user = User.objects.filter(username=username).first()
                elif not user and door_code:
                    c = DoorCode.objects.filter(code=door_code).first()
                    if c:
                        user = c.user

                new_event = DoorEvent.objects.create(timestamp=tz_timestamp, door=door, user=user, code=door_code, event_type=event_type, event_description=description)
        return Messages.SUCCESS_RESPONSE

    def mark_sync(self):
        # A successfull sync is a success
        self.success_ts = localtime(now())
        self.sync_ts = localtime(now())
        self.is_syncing = False
        self.save()

    def mark_success(self):
        self.success_ts = localtime(now())
        self.save()

    def force_sync(self):
        self.sync_ts = None
        self.save()

    def unresolved_logs(self):
        return self.gatekeeperlog_set.filter(keymaster=self, resolved=False)

    def logs_for_day(self, target_date=None):
        if not target_date:
            target_date = localtime(now())
        target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date + timedelta(days=1)
        logs_today = self.gatekeeperlog_set.filter(keymaster=self, timestamp__gte=target_date, timestamp__lt=end_date)
        logs_today = logs_today.order_by('timestamp').reverse()
        logger.debug("logs found for '%s': %d" % (target_date.date(), logs_today.count()))
        return logs_today

    def clear_logs(self, log_id=None):
        logs = self.unresolved_logs()
        if log_id:
            logs = logs.filter(id=log_id)
        for l in logs:
            l.resolved = True
            l.save()

    def log_message(self, message):
        # Save this message to the database
        GatekeeperLog.objects.create(keymaster=self, message=message)

        # How many have we seen today?
        logs_today = self.logs_for_day()
        cnt_today = logs_today.count()

        # Avoid a mailbombing the admins
        send_mail = False
        if cnt_today < 5:
            # Send the first 5 so we know there is an issue
            send_mail = True
        else:
            # We know there are more then 5 so we should check how fast they are coming
            delay = logs_today[0].timestamp - logs_today[1].timestamp
            if delay.seconds >= 600:
                # Send if there is more then a 10 minute gap between logs
                send_mail = True
            else:
                # Small delay between last 2 logs so they are coming in hot
                if cnt_today % 30 == 0:
                    # Send every 30th log
                    send_mail = True

        # Email the system admins of the problem
        if send_mail:
            logger.debug("mailing admins new gatekeeper log")
            mail.mail_admins("Gatekeeper Message", message, fail_silently=True)

    def __str__(self):
        return self.description


class Door(models.Model):
    name = models.CharField(max_length=16, unique=True)
    door_type = models.CharField(max_length=16, choices=DoorTypes.CHOICES)
    keymaster = models.ForeignKey(Keymaster, on_delete=models.CASCADE)
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
            tz = get_current_timezone()
            ts = str(last_event.timestamp.astimezone(tz))[:19].replace(" ", "T")
        return ts

    def __str__(self):
        return self.name


class DoorCode(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.CASCADE)
    modified_ts = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=32, unique=True)

    def get_last_event(self):
        return DoorEvent.objects.filter(code=self.code).order_by('timestamp').reverse().first()

    def __str__(self):
        return '%s: %s' % (self.user, self.code)

def door_code_callback(sender, **kwargs):
    door_code = kwargs['instance']
    # For now we are just going to force all keymasters to sync whenever a code is deleted
    # When codes are tied to specific doors we can make this smarter.
    for km in Keymaster.objects.filter(is_enabled=True):
        km.force_sync()
post_delete.connect(door_code_callback, sender=DoorCode)


class DoorEventManager(models.Manager):

    def users_for_day(self, day=None):
        if not day:
            day = localtime(now())
        start = datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)
        start = make_aware(start, get_current_timezone())
        end = start + timedelta(days=1)
        #logger.debug("users_for_day from '%s' to '%s'" % (start, end))
        return DoorEvent.objects.filter(timestamp__range=(start, end))


class DoorEvent(models.Model):
    objects = DoorEventManager()

    timestamp = models.DateTimeField(null=False)
    door = models.ForeignKey(Door, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, db_index=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=16, null=True)
    event_type = models.CharField(max_length=1, choices=DoorEventTypes.CHOICES, default=DoorEventTypes.UNKNOWN, null=False)
    event_description = models.CharField(max_length=256)

    def __str__(self):
        return '%s: %s' % (self.door, self.event_description)

class GatekeeperLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    keymaster = models.ForeignKey(Keymaster, on_delete=models.CASCADE)
    message = models.TextField()

    def __str__(self):
        return '%s: %s' % (self.timestamp, self.message)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
