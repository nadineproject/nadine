from datetime import datetime, time, date, timedelta
from collections import namedtuple

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.contrib.auth.models import User
from django.db import connection

from staff.models import Member, Membership

class UserDevice(models.Model):
	user = models.ForeignKey(User, null=True, unique=False)
	device_name = models.CharField(max_length=32, blank=True, null=True)
	mac_address = models.CharField(max_length=17, blank=False, null=False, unique=True)
	def __unicode__(self):
		if self.device_name: 
			return self.device_name
		return self.mac_address

class ArpLog_Manager(models.Manager):
	def for_range2(self, day_start, day_end):
		DeviceLog = namedtuple('DeviceLog', 'id, device, start, end')
		device_logs = []
		for arp_log in ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime'):
			found_it = False
			for l in device_logs:
				if l.id == arp_log.device.id:
					l._replace(end = arp_log.runtime)
					found_it = True
					break;
			if not found_it:
				device_logs.append(DeviceLog(arp_log.device.id, arp_log.device, arp_log.runtime, arp_log.runtime))
		return device_logs

	def for_range3(self, day_start, day_end):
		DeviceLog = namedtuple('DeviceLog', 'id, name, start, end')
		device_logs = {}
		for arp_log in ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime'):
			if log.device in device_logs:
				device_logs[log.device]._replace(end = arp_log.runtime)
			else:
				device_logs[log.device] = DeviceLog(arp_log.device.id, arp_log.device, arp_log.runtime, arp_log.runtime)
		return device_logs
		
	def for_range(self, day_start, day_end):
		DeviceLog = namedtuple('DeviceLog', 'device, start, end')
		sql = "select device_id, min(runtime), max(runtime) from arpwatch_arplog where runtime > '%s' and runtime < '%s' group by 1 order by 2;"
		sql = sql % (day_start, day_end)
		cursor = connection.cursor()
		cursor.execute(sql)
		device_logs = []
		for row in cursor.fetchall():
			device_logs.append(DeviceLog(UserDevice.objects.get(pk=row[0]), row[1], row[2]))
		return device_logs

#	def for_day(self):
# select device_id, max(runtime), min(runtime) from arpwatch_arplog 
# where runtime > '2011-05-16 00:00' and runtime < '2011-05-16 23:59' 
# group by device_id order by 2;
		
		
class ArpLog(models.Model):
	runtime = models.DateTimeField(blank=False)
	device = models.ForeignKey(UserDevice, null=False)
	ip_address = models.IPAddressField(blank=False, null=False)
	
	objects = ArpLog_Manager()
	class Meta:
	   ordering = ['-runtime']
	   get_latest_by = 'runtime'
	def __unicode__(self):
	   return '%s: %s = %s' % (self.runtime, self.ip_address, self.device.mac_address)

class UploadLog(models.Model):
	loadtime = models.DateTimeField(auto_now_add=True, null=False)
	user = models.ForeignKey(User, null=True, unique=False)
	file_name = models.CharField(max_length=32, blank=False, null=False)
	file_size = models.IntegerField(default=0)
	def __unicode__(self):
	   return '%s: %s = %s' % (self.loadtime, self.user, self.file_name)
	
# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
