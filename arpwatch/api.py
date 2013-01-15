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
from django.conf.urls import patterns, include, url
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect

import arp
from models import UserDevice, ArpLog
from staff.models import Member, Membership, DailyLog

class ActivityModel(object):
	'''
	The object which will hold the activity data to serve up via ActivityResource
	'''
	def __init__(self):
		now = datetime.now()
		midnight = now - timedelta(seconds=now.hour*60*60 + now.minute*60 + now.second)
		# These are the values which are directly exposed via the ActivityModel
		members = Member.objects.active_members()
		self.member_count = len(members)
		self.full_time_count = Membership.objects.by_date(now).filter(has_desk=True).count()
		self.part_time_counts = self.member_count - self.full_time_count
		devices = ArpLog.objects.for_range(midnight, now)
		self.device_count = len(devices)

	@property
	def here_today(self):
		'''This property is exposed in the ActivityModel'''
		results = []
		for member in arp.here_today():
			member_dict = {"username":member.user.username, "name":member.full_name}
			member_dict["photo"] = "http://%s%s%s" % (Site.objects.get_current().domain, settings.MEDIA_URL, member.photo)
			member_dict["industry"] = member.industry
			membership = member.membership_type()
			member_dict["membership"] = membership
			tags = []
			for t in member.tags.all():
				tags.append(t)
			member_dict["tags"] = tags
			results.append(member_dict)
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
	here_today = fields.ListField(attribute='here_today', readonly=True)

	class Meta:
		allowed_methods = ['get']
		#authentication = SessionAuthentication()
		#authorization = DjangoAuthorization()

	def detail_uri_kwargs(self, bundle_or_obj): return {'pk': '0'}
	def get_object_list(self, request): return [self.obj_get({'pk':0})]
	def obj_get_list(self, request=None, **kwargs): return self.get_object_list(request)
	def obj_get(self, request=None, **kwargs): return ActivityModel()
