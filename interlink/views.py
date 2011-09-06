import calendar
import traceback
from datetime import datetime, timedelta, date

from django.db.models import Q
from django.contrib import auth
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import feedgenerator
from django.utils.html import strip_tags
from django.template import RequestContext
from django.template import Context, loader
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment
from django.template.loader import render_to_string
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
import django.contrib.contenttypes.models as content_type_models
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect

from models import MailingList, IncomingMail

def index(request):
   return render_to_response('interlink/index.html', {}, context_instance=RequestContext(request))

@staff_member_required
def list(request, id):
   mailing_list = get_object_or_404(MailingList, pk=id)
   return render_to_response('interlink/list.html', {'mailing_list':mailing_list}, context_instance=RequestContext(request))

@login_required
def moderator_list(request):
   return render_to_response('interlink/moderator_list.html', {}, context_instance=RequestContext(request))
   
@login_required
def moderator_inspect(request, id):
   incoming_mail = get_object_or_404(IncomingMail, pk=id)
   return render_to_response('interlink/moderator_inspect.html', {'incoming_mail':incoming_mail}, context_instance=RequestContext(request))

@login_required
def moderator_approve(request, id):
   incoming_mail = get_object_or_404(IncomingMail, pk=id)
   if not request.user in incoming_mail.mailing_list.moderators.all():
      print request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name
      return HttpResponseRedirect(reverse('interlink.views.moderator_list'))

   if incoming_mail.state != 'moderate': 
      print 'Tried to moderate an email which needs no moderation.'
      return HttpResponseRedirect(reverse('interlink.views.moderator_list'))

   incoming_mail.create_outgoing()
   return HttpResponseRedirect(reverse('interlink.views.moderator_list'))

@login_required
def moderator_reject(request, id):
   incoming_mail = get_object_or_404(IncomingMail, pk=id)
   if not request.user in incoming_mail.mailing_list.moderators.all():
      print request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name
      return HttpResponseRedirect(reverse('interlink.views.moderator_list'))

   if incoming_mail.state != 'moderate': 
      print 'Tried to moderate an email which needs no moderation.'
      return HttpResponseRedirect(reverse('interlink.views.moderator_list'))

   incoming_mail.reject()
   return HttpResponseRedirect(reverse('interlink.views.moderator_list'))



# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
