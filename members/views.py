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

from staff.models import Member
from interlink.forms import MailingListSubscriptionForm

@login_required
def index(request):
	return render_to_response('members/index.html',{  'members':Member.objects.active_members().order_by('user__first_name') }, context_instance=RequestContext(request))

@login_required
def user(request, username):
	user = get_object_or_404(User, username=username)
	return render_to_response('members/user.html',{'user':user}, context_instance=RequestContext(request))

@login_required
def mail(request, username):
	user = get_object_or_404(User, username=username)
	if not user == request.user or request.user.is_staff: return HttpResponseRedirect(reverse('members.views.mail', kwargs={'username':request.user.username}))
	if request.method == 'POST':
		sub_form = MailingListSubscriptionForm(request.POST)
		if sub_form.is_valid():
			print sub_form.cleaned_data
			sub_form.save(user)
			return HttpResponseRedirect(reverse('members.views.mail', kwargs={'username':user.username}))
	return render_to_response('members/mail.html',{'user':user, 'mailing_list_subscription_form':MailingListSubscriptionForm()}, context_instance=RequestContext(request))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
