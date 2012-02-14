from datetime import datetime, time, date, timedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.contrib.auth.models import User

from staff.models import Member, Membership

class MACAddress(models.Model):
	value = models.CharField(max_length=12, blank=False, null=False)
	user = models.ForeignKey(User, null=True, unique=False)
	computer_name = models.CharField(max_length=32, blank=True, null=True)
	def __unicode__(self):
	   return '%s:%s:%s:%s:%s:%s' % (self.value[0-1], self.value[2-3], self.value[4-5], self.value[6-7], self.value[8-9], self.value[10-11])
	
class IPAddress(models.Model):
	value = models.CharField(max_length=12, blank=False, null=False, unique=True)
	def __unicode__(self):
	   return '%s.%s.%s.%s' % (self.value[0-2], self.value[3-5], self.value[6-8], self.value[9-11])
	
class ArpLog(models.Model):
	"""A record of when the ARP table was pulled"""
	runtime = models.DateTimeField(auto_now_add=True)
	class Meta:
	   ordering = ['-runtime']
	   get_latest_by = 'runtime'
	def __unicode__(self):
	   return 'ArpLog %s' % (self.runtime)

class ArpLogEntry(models.Model):
	log = models.ForeignKey(ArpLog, null=False, unique=False)
	mac = models.ForeignKey(MACAddress, null=False, unique=True)
	ip = models.ForeignKey(IPAddress, null=True, unique=False)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
