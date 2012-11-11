import traceback

from tastypie import fields
from tastypie.api import Api
from tastypie.paginator import Paginator
from datetime import datetime, timedelta, date
from tastypie.validation import FormValidation
from tastypie.authentication import Authentication, SessionAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import patterns, include, url
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect

from nadine import API
from models import UserDevice, ArpLog
from staff.models import Member, Membership, DailyLog

class ActivityModel(object):
	'''
	The object which will hold the activity data to serve up via ActivityResource
	'''
	def __init__(self):

		self._here_today = {}

		now = datetime.now()
		# Who's signed into the space today
		daily_logs = DailyLog.objects.filter(visit_date=now)
		for l in daily_logs:
			self._here_today[l.member] = l.created

		# Device Logs
		midnight = now - timedelta(seconds=now.hour*60*60 + now.minute*60 + now.second)
		device_logs = ArpLog.objects.for_range(midnight, now)
		for l in device_logs:
			if l.device.user:
				member = l.device.user.get_profile()
				if not self._here_today.has_key(member) or l.start < self._here_today[member]:				
					self._here_today[member] = l.start

		# These are the values which are directly exposed via the ActivityModel
		self.member_count = Member.objects.active_members().count()
		self.full_time_count = Membership.objects.by_date(now).filter(has_desk=True).count()
		self.part_time_counts = self.member_count - self.full_time_count
		self.device_count = len(device_logs)

	@property
	def here_today(self):
		'''This property is exposed in the ActivityModel'''
		results = {}
		for member, created in self._here_today.iteritems():
			results[member.user.username] = created
		return results

class ActivityResource(Resource):
	'''
	Exposes information about the activity in the space for today.
	There will only ever be one resource listed and it will always have a pk of '0'
	The URL to the resource is /api/v1/activity/0/
	The URL to the list of all resources is /api/v1/activity/
	'''
	member_count = fields.IntegerField(attribute='member_count', readonly=True)
	full_time_count = fields.IntegerField(attribute='full_time_count', readonly=True)
	part_time_counts = fields.IntegerField(attribute='part_time_counts', readonly=True)
	device_count = fields.IntegerField(attribute='device_count', readonly=True)
	here_today = fields.DictField(attribute='here_today', readonly=True)

	class Meta:
		allowed_methods = ['get']
		#authentication = SessionAuthentication()
		#authorization = DjangoAuthorization()

	def detail_uri_kwargs(self, bundle_or_obj): return {'pk': '0'}
	def get_object_list(self, request): return [self.obj_get({'pk':0})]
	def obj_get_list(self, request=None, **kwargs): return self.get_object_list(request)
	def obj_get(self, request=None, **kwargs): return ActivityModel()

API.register(ActivityResource())
