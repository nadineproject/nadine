import os, traceback, logging, uuid
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
from django.template.loader import render_to_string
from django.utils import timezone
from staff.models import Member, DailyLog, Bill, FileUpload
from staff.forms import NewUserForm, MemberSearchForm
from arpwatch import arp
from staff import email
from forms import SignatureForm

from easy_pdf.rendering import render_to_pdf, render_to_pdf_response

logger = logging.getLogger(__name__)

def members(request):
	members = None
	list_members = request.GET.has_key("startswith")
	if list_members:
		sw = request.GET.get('startswith')
		members = Member.objects.active_members().filter(user__first_name__startswith=sw).order_by('user__first_name')
	return render_to_response('tablet/members.html', {'members':members, 'list_members':list_members}, context_instance=RequestContext(request))

def here_today(request):
	members = arp.users_for_day()
	return render_to_response('tablet/here_today.html', {'members':members}, context_instance=RequestContext(request))

def visitors(request):
	page_message = None
	if request.method == "POST":
		form = NewUserForm(request.POST)
		try:
			if form.is_valid():
				user = form.save() 
				return HttpResponseRedirect(reverse('tablet.views.post_create', kwargs={ 'username':user.username }))
		except Exception as e:
			page_message = str(e)[3:len(str(e))-2]
			logger.error(str(e))
			#page_message = str(e)
	else:
		form = NewUserForm()
	return render_to_response('tablet/visitors.html', {'new_user_form':form, 'page_message':page_message}, context_instance=RequestContext(request))

def search(request):
	search_results = None
	if request.method == "POST":
		member_search_form = MemberSearchForm(request.POST)
		if member_search_form.is_valid(): 
			search_results = Member.objects.search(member_search_form.cleaned_data['terms'])
	else:
		member_search_form = MemberSearchForm()
	return render_to_response('tablet/search.html', { 'member_search_form':member_search_form, 'search_results':search_results }, context_instance=RequestContext(request))

def user_profile(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	membership = member.active_membership()
	tags = member.tags.order_by('name')
	return render_to_response('tablet/user_profile.html',{'user':user, 'member':member, 'membership':membership, 'tags':tags}, context_instance=RequestContext(request))

def user_signin(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	membership = member.active_membership()

	can_signin = False
	last_membership = member.last_membership()
	if not last_membership or last_membership.end_date or not last_membership.has_desk:
		if not DailyLog.objects.filter(member=member, visit_date=timezone.localtime(timezone.now()).date()):
			can_signin = True

	search_results = None
	if request.method == "POST":
		member_search_form = MemberSearchForm(request.POST)
		if member_search_form.is_valid(): 
			search_results = Member.objects.search(member_search_form.cleaned_data['terms'], active_only=True)
	else:
		member_search_form = MemberSearchForm()

	return render_to_response('tablet/user_signin.html',{'user':user, 'member':member, 'can_signin':can_signin, 
		'membership':membership, 'member':member, 'member_search_form':member_search_form, 'search_results':search_results}, context_instance=RequestContext(request))

def post_create(request, username):
	user = get_object_or_404(User, username=username)
	if request.POST.has_key("work_today"):
		work_today = request.POST.get('work_today')
		if work_today == "Yes":
			# Send them over to the sign-in page.  This will trigger the Free Trial logic down the line.
			return HttpResponseRedirect(reverse('tablet.views.signin_user', kwargs={ 'username':user.username }))
		else:
			try:
				email.announce_new_user(user)
			except:
				logger.error("Could not send introduction email to %s" % user.email)
			return HttpResponseRedirect(reverse('tablet.views.members', kwargs={}))
	return render_to_response('tablet/post_create.html',{'user':user}, context_instance=RequestContext(request))

def signin_user(request, username):
	return signin_user_guest(request, username, None)

def signin_user_guest(request, username, guestof):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	daily_log = DailyLog()
	daily_log.member = member
	daily_log.visit_date = timezone.localtime(timezone.now()).date()
	# Only proceed if they haven't signed in already
	if DailyLog.objects.filter(member=member, visit_date=daily_log.visit_date).count() == 0:
		if guestof:
			guestof_user = get_object_or_404(User, username=guestof)
			guestof_member = get_object_or_404(Member, user=guestof_user)
			daily_log.guest_of = guestof_member
		if DailyLog.objects.filter(member=member).count() == 0:
			daily_log.payment = 'Trial';
		else:
			daily_log.payment = 'Bill';
		daily_log.save()
	
		if daily_log.payment == 'Trial':
			try:
				email.announce_free_trial(user)
				email.send_introduction(user)
				email.subscribe_to_newsletter(user)
			except:
				logger.error("Could not send introduction email to %s" % user.email)
		else:
			if member.onboard_tasks_to_complete() > 0:
				email.announce_tasks_todo(user, member.onboard_tasks_incomplete())
	return HttpResponseRedirect(reverse('tablet.views.welcome', kwargs={'username':username}))

def welcome(request, username):
	usage_color = "black";
	user = get_object_or_404(User, username=username)
	member = user.get_profile()
	membership = None
	if member:
		membership = member.active_membership()
		if membership:
			days = len(member.activity_this_month())
			allowed = membership.get_allowance()
			if days > allowed:
				usage_color = "red"
			elif days == allowed:
				usage_color = "orange"
			else:
				usage_color = "green"
	motd = settings.MOTD
	timeout = settings.MOTD_TIMEOUT
	return render_to_response('tablet/welcome.html', {'user':user, 'member':member, 'membership':membership, 
		'motd':motd, 'timeout':timeout, 'usage_color':usage_color}, context_instance=RequestContext(request))

def signature_capture(request, username):
	user = get_object_or_404(User, username=username)
	today = timezone.localtime(timezone.now()).date()
	pdf_file = None
	form = SignatureForm(request.POST or None)
	if form and form.has_signature():
		signature_file = form.save_signature()
		pdf_data = render_to_pdf('tablet/signature_render.html', {'name':user.get_full_name, 'date':today, 'signature_file':signature_file})
		# TODO - dynamic document type
		document_type = FileUpload.MEMBER_AGMT
		pdf_file = FileUpload.objects.pdf_from_string(user, pdf_data, document_type, user)
		# TODO - Delete signature file
	return render_to_response('tablet/signature_capture.html', {'user':user, 'form':form, 'today':today, 'pdf_file':pdf_file}, context_instance=RequestContext(request))

def signature_render(request, username, signature_file):
	user = get_object_or_404(User, username=username)
	today = timezone.localtime(timezone.now()).date()
	return render_to_pdf_response(request, 'tablet/signature_render.html', {'name':user.get_full_name, 'date':today, 'signature_file':signature_file})

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
