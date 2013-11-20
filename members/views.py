import traceback, string
from datetime import date, datetime, timedelta
from operator import itemgetter, attrgetter

from django.conf import settings
from django.template import RequestContext, Template
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from staff.models import Member, Membership, Transaction, DailyLog
from forms import EditProfileForm
from interlink.forms import MailingListSubscriptionForm
from interlink.models import IncomingMail
from models import HelpText, UserNotification
from arpwatch import arp
from arpwatch.models import ArpLog, UserDevice

@login_required
def home(request):
	title = "Home"
	template_text = "Welcome to {{ site.name }}"
	other_topics = {}
	for topic in HelpText.objects.all():
		if topic.slug == 'home':
			title = topic.title
			template_text = topic.template
		else: 
			other_topics[topic.title] = topic
	
	current_context = RequestContext(request)
	template = Template(template_text)
	rendered = template.render(current_context)
	return render_to_response('members/home.html',{'title':title, 'page_body':rendered, 'other_topics':other_topics}, current_context)

@login_required
def help_topic(request, slug):
	topic = get_object_or_404(HelpText, slug=slug)
	title = topic.title
	template_text = topic.template
	current_context = context_instance=RequestContext(request)
	template = Template(template_text)
	rendered = template.render(current_context)
	return render_to_response('members/help_topic.html',{'title':title, 'page_body':rendered}, current_context)

@login_required
def all_members(request):
	members = Member.objects.active_members().order_by('user__first_name') 
	return render_to_response('members/all_members.html',{ 'members':members }, context_instance=RequestContext(request))

@login_required
def here_today(request):
	members = arp.users_for_day()
	return render_to_response('members/here_today.html',{ 'members':members }, context_instance=RequestContext(request))

def not_active(request):
	return render_to_response('members/not_active.html',{ }, context_instance=RequestContext(request))

@login_required
def profile_redirect(request):
	return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))

@login_required
def user(request, username):
	user = get_object_or_404(User, username=username)
	member = get_object_or_404(Member, user=user)
	activity = DailyLog.objects.filter(member=member, payment='Bill', bills__isnull=True, visit_date__gt=timezone.now().date()-timedelta(days=31))
	guest_activity = DailyLog.objects.filter(guest_of=member, payment='Bill', guest_bills__isnull=True, visit_date__gte=timezone.now().date()-timedelta(days=31))
	return render_to_response('members/user.html',{'user':user, 'member':member, 'activity':activity, 'guest_activity':guest_activity, 'settings':settings}, context_instance=RequestContext(request))

@login_required
def mail(request, username):
	user = get_object_or_404(User, username=username)
	if not user == request.user: return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))
	if request.method == 'POST':
		sub_form = MailingListSubscriptionForm(request.POST)
		if sub_form.is_valid():
			sub_form.save(user)
			return HttpResponseRedirect(reverse('members.views.mail', kwargs={'username':user.username}))
	return render_to_response('members/mail.html',{'user':user, 'mailing_list_subscription_form':MailingListSubscriptionForm()}, context_instance=RequestContext(request))

@login_required
def mail_message(request, id):
	message = get_object_or_404(IncomingMail, id=id)
	return render_to_response('members/mail_message.html',{'message':message}, context_instance=RequestContext(request))

@login_required
def edit_profile(request, username):
	user = get_object_or_404(User, username=username)
	member = user.get_profile()

	if request.method == 'POST':
		profile_form = EditProfileForm(request.POST, request.FILES)
		if profile_form.is_valid():
			profile_form.save()
			return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':user.username}))
	else:
		profile_form = EditProfileForm(initial={'member_id':member.id, 'phone':member.phone, 'phone2':member.phone2, 'email2':member.email2,
			'address1':member.address1, 'address2':member.address2, 'city':member.city, 'state':member.state, 'zipcode':member.zipcode,
			'company_name':member.company_name, 'url_personal':member.url_personal, 'url_professional':member.url_professional, 
			'url_facebook':member.url_facebook, 'url_twitter':member.url_twitter, 'url_biznik':member.url_biznik, 
			'url_linkedin':member.url_linkedin, 'url_aboutme':member.url_aboutme, 'url_github':member.url_github, 
			'gender':member.gender, 'howHeard':member.howHeard, 'industry':member.industry, 'neighborhood':member.neighborhood, 
			'has_kids':member.has_kids, 'self_employed':member.self_employed})

	return render_to_response('members/edit_profile.html',{'user':user, 'profile_form':profile_form}, context_instance=RequestContext(request))

@login_required
def receipt(request, username, id):
	user = get_object_or_404(User, username=username)
	if not user == request.user: 
		if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))
	transaction = get_object_or_404(Transaction, id=id);
	if not user.profile == transaction.member: 
		if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))
	bills = transaction.bills.all()
	return render_to_response('members/receipt.html',{'user':user, 'transaction':transaction, 'bills':bills}, context_instance=RequestContext(request))

@login_required
def tags(request):
	tags = []
	for tag in Member.tags.all().order_by('name'):
		members = Member.objects.active_members().filter(tags__name__in=[tag])
		if members:
			tags.append((tag, members))
	return render_to_response('members/tags.html',{'tags':tags}, context_instance=RequestContext(request))

@login_required
def tag_cloud(request):
	tags = []
	for tag in Member.tags.all().order_by('name'):
		members = Member.objects.active_members().filter(tags__name__in=[tag])
		if members:
			tags.append((tag, members))
	return render_to_response('members/tag_cloud.html',{'tags':tags}, context_instance=RequestContext(request))

@login_required
def tag(request, tag):
	members = Member.objects.active_members().filter(tags__name__in=[tag])
	return render_to_response('members/tag.html',{'tag':tag, 'members':members}, context_instance=RequestContext(request))

@login_required
def user_tags(request, username):
	user = get_object_or_404(User, username=username)
	if not user == request.user: 
		if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))
	profile = user.get_profile()
	user_tags = profile.tags.all()
	
	error = None
	if request.method == 'POST':
		tag = request.POST.get('tag')
		if tag:
			for p in string.punctuation:
				if p in tag:
					error = "Tags can't contain punctuation."
					break;
			else:
				profile.tags.add(tag.lower())

	all_tags = Member.tags.all()
	return render_to_response('members/user_tags.html',{'user':user, 'user_tags':user_tags, 'all_tags':all_tags, 'error':error}, context_instance=RequestContext(request))

@login_required
def delete_tag(request, username, tag):
	user = get_object_or_404(User, username=username)
	if not user == request.user: 
		if not request.user.is_staff: return HttpResponseRedirect(reverse('members.views.user', kwargs={'username':request.user.username}))
	user.get_profile().tags.remove(tag)
	return HttpResponseRedirect(reverse('members.views.user_tags', kwargs={'username':request.user.username}))

@login_required
def user_devices(request):
	user = request.user
	profile = user.get_profile()

	error = None
	if request.method == 'POST':
		device_id = request.POST.get('device_id')
		device = UserDevice.objects.get(id=device_id)

		action = request.POST.get('action')
		if action == "Register":
			device.user = user

		device_name = request.POST.get('device_name')
		device_name = device_name.strip()[:32]
		device.device_name = device_name
		device.save()

	devices = arp.devices_by_user(user)
	ip = request.META['REMOTE_ADDR']
	this_device = arp.device_by_ip(ip)
	return render_to_response('members/user_devices.html',{'user':user, 'devices':devices, 'this_device':this_device, 'ip':ip, 'error':error}, context_instance=RequestContext(request))

@login_required
def notifications(request):
	notifications = UserNotification.objects.filter(notify_user=request.user, sent_date__isnull=True)
	return render_to_response('members/notifications.html',{'notifications':notifications}, context_instance=RequestContext(request))

@login_required
def add_notification(request, username):
	target = get_object_or_404(User, username=username)
	if UserNotification.objects.filter(notify_user=request.user, target_user=target).count() == 0:
		UserNotification.objects.create(notify_user=request.user, target_user=target)	
	return HttpResponseRedirect(reverse('members.views.notifications', kwargs={}))

@login_required
def delete_notification(request, username):
	target = get_object_or_404(User, username=username)
	for n in UserNotification.objects.filter(notify_user=request.user, target_user=target):
		n.delete()
	return HttpResponseRedirect(reverse('members.views.notifications', kwargs={}))

def ticker(request):
	here_today = arp.users_for_day()
	
	now = timezone.localtime(timezone.now())
	midnight = now - timedelta(seconds=now.hour*60*60 + now.minute*60 + now.second)
	device_logs = ArpLog.objects.for_range(midnight, now)
	
	counts = {}
	counts['members'] = Member.objects.active_members().count()
	counts['full_time'] = Membership.objects.by_date(now).filter(has_desk=True).count()
	counts['part_time'] = counts['members'] - counts['full_time']
	counts['here_today'] = len(here_today)
	counts['devices'] = len(device_logs)
	
	# Auto refresh?
	refresh = True;
	if request.GET.has_key("norefresh"):
		refresh = False;
		
	return render_to_response('members/ticker.html',{'counts':counts, 'members':here_today, 'refresh':refresh}, context_instance=RequestContext(request))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
