from datetime import datetime, time, date, timedelta
from collections import OrderedDict, namedtuple

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Min, Max
from django.utils import timezone

from nadine.models import Member, Membership

class UserDevice(models.Model):
	user = models.ForeignKey(User, blank=True, null=True, unique=False)
	device_name = models.CharField(max_length=32, blank=True, null=True)
	mac_address = models.CharField(max_length=17, blank=False, null=False, unique=True, db_index=True)
	ignore = models.BooleanField(default=False)
	def __unicode__(self):
		if self.user:
			return self.user.__unicode__()
		if self.device_name: 
			return self.device_name
		return self.mac_address

class UserRemoteAddr(models.Model):
	logintime = models.DateTimeField(blank=False)
	user = models.ForeignKey(User, blank=False, null=False, unique=False)
	ip_address = models.IPAddressField(blank=False, null=False)
	class Meta:
	   ordering = ['-logintime']
	   get_latest_by = 'logintime'
	def __unicode__(self):
	   return '%s: %s = %s' % (self.logintime, self.user, self.ip_address)
	
class ArpLog_Manager(models.Manager):
	def for_range(self, day_start, day_end):
		device_logs = OrderedDict()
		DeviceLog = namedtuple('DeviceLog', 'device, start, end, diff')
		for arp_log in ArpLog.objects.filter(runtime__gte=day_start, runtime__lte=day_end, device__ignore=False).order_by('runtime'):
			key = arp_log.device.mac_address
			if key in device_logs:
				start = device_logs[key].start
				end = arp_log.runtime
				device_logs[key] = DeviceLog(arp_log.device, start, end, end-start)
			else:
				# Create a new device log
				start = end = arp_log.runtime
				device_logs[key] = DeviceLog(arp_log.device, start, end, 0)
		return device_logs.values()
			
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

class ArpLog(models.Model):
	runtime = models.DateTimeField(blank=False, db_index=True)
	device = models.ForeignKey(UserDevice, null=False)
	ip_address = models.IPAddressField(blank=False, null=False, db_index=True)
	
	objects = ArpLog_Manager()
	class Meta:
	   ordering = ['-runtime']
	   get_latest_by = 'runtime'
	def __unicode__(self):
	   return '%s: %s = %s' % (self.runtime, self.ip_address, self.device.mac_address)

class ImportLog(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	file_name = models.CharField(max_length=32, blank=False, null=False, db_index=True)
	success = models.BooleanField(default=False)
	def __unicode__(self):
	   return '%s: %s = %s' % (self.created, self.file_name, self.success)
	
# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
