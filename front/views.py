import datetime
import calendar
import pprint
import traceback

from django.conf import settings
from django.db.models import Q
from django.template import Context, loader
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
import django.contrib.contenttypes.models as content_type_models
from django.template import RequestContext
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.utils import feedgenerator
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.views.decorators.csrf import csrf_protect

from models import *

def index(request):
	return HttpResponseRedirect(reverse('staff.views.todo'))

@csrf_protect
def password_reset(request, is_admin_site=False, template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', password_reset_form=PasswordResetForm, token_generator=default_token_generator,post_reset_redirect=None):
   if post_reset_redirect is None: post_reset_redirect = reverse('django.contrib.auth.views.password_reset_done')
   if request.method == 'GET' and request.GET.get('email',None):
      form = password_reset_form(initial={'email':request.GET.get('email')})
   elif request.method == "POST":
      form = password_reset_form(request.POST)
      if form.is_valid():
         opts = {}
         opts['use_https'] = request.is_secure()
         opts['token_generator'] = token_generator
         if is_admin_site:
            opts['domain_override'] = request.META['HTTP_HOST']
         else:
            opts['email_template_name'] = email_template_name
            if not Site._meta.installed:
               opts['domain_override'] = RequestSite(request).domain
         form.save(**opts)
         return HttpResponseRedirect(post_reset_redirect)
   else:
      form = password_reset_form()
   return render_to_response(template_name, {'form': form}, context_instance=RequestContext(request))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
