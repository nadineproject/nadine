import logging
from datetime import datetime, time, date, timedelta
from collections import OrderedDict, namedtuple

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db import connection
from django.db.models import Min, Max
from django.utils.timezone import localtime, now
from django.conf import settings

from nadine.models.membership import Membership
from nadine.utils import network

logger = logging.getLogger(__name__)

class UserDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, unique=False, on_delete=models.CASCADE)
    device_name = models.CharField(max_length=32, blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=False, null=False, unique=True, db_index=True)
    ignore = models.BooleanField(default=False)

    @property
    def last_seen(self):
        last_log = self.arplog_set.order_by('-runtime').first()
        return last_log.runtime

    def __str__(self):
        if self.user:
            return self.user.__str__()
        if self.device_name:
            return self.device_name
        return self.mac_address


class UserRemoteAddr(models.Model):
    logintime = models.DateTimeField(blank=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, null=False, unique=False, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(blank=False, null=False)

    class Meta:
        ordering = ['-logintime']
        get_latest_by = 'logintime'

    def __str__(self):
        return '%s: %s = %s' % (self.logintime, self.user, self.ip_address)


# Signal to create a new UserRemoreAddr when people login
def register_user_ip(sender, user, request, **kwargs):
    logtime = localtime(now())
    ip = network.get_addr(request)
    if ip:
        ip_log = UserRemoteAddr.objects.create(logintime=logtime, user=user, ip_address=ip)
    logger.info("register_user_ip: Address for %s = %s @ %s" % (user, ip, logtime))
user_logged_in.connect(register_user_ip)


class ArpLog_Manager(models.Manager):

    def for_range(self, day_start, day_end):
        device_logs = OrderedDict()
        DeviceLog = namedtuple('DeviceLog', 'device, start, end, diff')
        for arp_log in ArpLog.objects.filter(runtime__gte=day_start, runtime__lte=day_end, device__ignore=False).order_by('runtime'):
            key = arp_log.device.mac_address
            if key in device_logs:
                start = device_logs[key].start
                end = arp_log.runtime
                device_logs[key] = DeviceLog(arp_log.device, start, end, end - start)
            else:
                # Create a new device log
                start = end = arp_log.runtime
                device_logs[key] = DeviceLog(arp_log.device, start, end, 0)
        return list(device_logs.values())

    def for_device(self, device_id):
        DeviceLog = namedtuple('DeviceLog', 'ip, day')
        sql = "select ip_address, date_trunc('day', runtime) from arpwatch_arplog where device_id = %s group by 1, 2 order by 2 desc;"
        sql = sql % (device_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        device_logs = []
        for row in cursor.fetchall():
            device_logs.append(DeviceLog(row[0], row[1]))
        return device_logs

    def for_user(self, username, day_start, day_end):
        user = User.objects.get(username=username)
        device_logs = OrderedDict()
        DeviceLog = namedtuple('DeviceLog', 'start, end, diff')
        logs = ArpLog.objects.filter(device__user=user, runtime__range=(day_start, day_end)).order_by('runtime')
        for arp_log in logs:
            local_time = localtime(arp_log.runtime)
            key = local_time.date()
            if key in device_logs:
                start = device_logs[key].start
                end = arp_log.runtime
                device_logs[key] = DeviceLog(start, end, end - start)
            else:
                # Create a new device log
                start = end = arp_log.runtime
                device_logs[key] = DeviceLog(start, end, 0)
        return list(device_logs.values())


class ArpLog(models.Model):
    runtime = models.DateTimeField(blank=False, db_index=True)
    device = models.ForeignKey(UserDevice, null=False, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(blank=False, null=False, db_index=True)

    objects = ArpLog_Manager()

    class Meta:
        ordering = ['-runtime']
        get_latest_by = 'runtime'

    def __str__(self):
        return '%s: %s = %s' % (self.runtime, self.ip_address, self.device.mac_address)


class ImportLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=32, blank=False, null=False, db_index=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return '%s: %s = %s' % (self.created, self.file_name, self.success)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
