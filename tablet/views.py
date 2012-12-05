import traceback
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404

from staff.models import Member, DailyLog, Bill
from staff.forms import NewUserForm, MemberSearchForm
from django.core.mail import send_mail

from arpwatch import arp

@login_required
def new_user(request):
	page_message = None
	if request.method == "POST":
		form = NewUserForm(request.POST)
		try:
			if form.is_valid():
				user = form.save() 
				# Send a welcome email
				site = Site.objects.get_current()
				url = "http://%s%s" % (site.domain, reverse('members.views.home'))
				subject = "%s: Introduction to Nadine" % (site.name)
				message = "Hello,\r\n\r\n \tWe just created a new user in Nadine, the system we use to run %s.  You can login to Nadine to see other members, update your profile, and view your activity and billing history.  The first time you will need to reset your password.  Your username is: %s\r\n\r\n%s\r\n\r\n - Nadine" % (site.name, user.username, url)
				send_mail(subject, message, settings.EMAIL_ADDRESS, [user.email], fail_silently=True)
				# Now sign them in
				return HttpResponseRedirect(reverse('tablet.views.signin_user', kwargs={ 'username':user.username }))
		except Exception as e:
			page_message = e
	else:
		form = NewUserForm()

	return render_to_response('tablet/new_user.html', {'new_user_form':form, 'page_message':page_message}, context_instance=RequestContext(request))

@login_required
def signin(request):
	members = []
	for member in Member.objects.active_members().order_by('user__first_name'):
		if not member.last_membership().has_desk:
			daily_logs = DailyLog.objects.filter(member=member, visit_date=datetime.today().date())
			if not daily_logs:
				members.append(member)
	
	return render_to_response('tablet/signin.html', {'members':members, 'member_search_form':MemberSearchForm()}, context_instance=RequestContext(request))

@login_required
def members(request):
	members = Member.objects.active_members().order_by('user__first_name')
	return render_to_response('tablet/members.html', {'members':members}, context_instance=RequestContext(request))

@login_required
def here_today(request):
	members = arp.here_today()
	return render_to_response('tablet/here_today.html', {'members':members}, context_instance=RequestContext(request))

@login_required
def search(request):
	search_results = None
	if request.method == "POST":
		member_search_form = MemberSearchForm(request.POST)
		if member_search_form.is_valid(): 
			search_results = Member.objects.search(member_search_form.cleaned_data['terms'])
	else:
		member_search_form = MemberSearchForm()
	return render_to_response('tablet/search.html', { 'member_search_form':member_search_form, 'search_results':search_results }, context_instance=RequestContext(request))

@login_required
def view_profile(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	tags = member.tags.order_by('name')
	return render_to_response('tablet/view_profile.html',{'user':user, 'member':member, 'tags':tags}, context_instance=RequestContext(request))

@login_required
def user_signin(request, username):
	print("member")
	
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	
	can_signin = False
	if not member.last_membership() or member.last_membership().end_date or not member.last_membership().has_desk:
			if not DailyLog.objects.filter(member=member, visit_date=datetime.today().date()):
			 	can_signin = True

	activity = DailyLog.objects.filter(member=member, payment='Bill', bills__isnull=True, visit_date__gt=date.today()-timedelta(days=31))
	guest_activity = DailyLog.objects.filter(guest_of=member, payment='Bill', guest_bills__isnull=True, visit_date__gte=date.today()-timedelta(days=31))

	search_results = None
	if request.method == "POST":
		member_search_form = MemberSearchForm(request.POST)
		if member_search_form.is_valid(): 
			search_results = Member.objects.search(member_search_form.cleaned_data['terms'])
	else:
		member_search_form = MemberSearchForm()

	return render_to_response('tablet/user_signin.html',{'user':user, 'member':member, 'can_signin':can_signin, 
		'activity':activity, 'guest_activity':guest_activity, 'member_search_form':member_search_form, 'search_results':search_results}, context_instance=RequestContext(request))

@login_required
def signin_user(request, username):
	return signin_user_guest(request, username, None)

@login_required
def signin_user_guest(request, username, guestof):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	daily_log = DailyLog()
	daily_log.member = member
	daily_log.visit_date = date.today()
	if guestof:
		guestof_user = get_object_or_404(User, username=guestof)
		guestof_member = get_object_or_404(Member, user=guestof_user)
		daily_log.guest_of = guestof_member
	if DailyLog.objects.filter(member=member).count() == 0:
		daily_log.payment = 'Trial';
		subject = "New User - %s" % (member)
		message = "Team,\r\n\r\n \t%s just signed in for the first time!\r\n\r\n - Nadine" % (member)
		send_mail(subject, message, settings.EMAIL_ADDRESS, [settings.TEAM_EMAIL_ADDRESS], fail_silently=True)
	else:
		daily_log.payment = 'Bill';
		if not member.photo:
			subject = "Photo Opportunity - %s" % (member)
			message = "Team,\r\n\r\n \t%s just signed in and we don't have a photo of them yet.\r\n\r\n - Nadine" % (member)
			send_mail(subject, message, settings.EMAIL_ADDRESS, [settings.TEAM_EMAIL_ADDRESS], fail_silently=True)

	daily_log.save()
	
		
	return HttpResponseRedirect(reverse('tablet.views.signin', kwargs={}))

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
