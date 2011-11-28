import traceback
from datetime import date, datetime, timedelta

from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from staff.models import Member, DailyLog


@staff_member_required
def index(request):
	view_daily = view_members = view_users = False
	view = request.GET.get("view", "daily")
	if view == "daily": 
		view_daily = True 
		members = Member.objects.daily_members();
	if view == "members": 
		view_members = True 
		members = Member.objects.active_members().order_by('user__first_name');
	if view == "users": 
		view_users = True 
		members = Member.objects.all().order_by('user__first_name');
	return render_to_response('tablet/index.html', {'members':members, 'view_daily':view_daily, 'view_members':view_members, 'view_users':view_users}, context_instance=RequestContext(request))

@staff_member_required
def user(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	return render_to_response('tablet/user.html',{'user':user, 'member':member}, context_instance=RequestContext(request))

@staff_member_required
def signin(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	daily_log = DailyLog()
	daily_log.member = member
	daily_log.visit_date = date.today()
	daily_log.payment = 'Bill';
	daily_log.save()
	return HttpResponseRedirect(reverse('tablet.views.index', kwargs={}))

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
