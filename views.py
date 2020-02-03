import datetime
import calendar
import pprint
import traceback
import logging

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
import django.contrib.contenttypes.models as content_type_models
from django.template import RequestContext
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import feedgenerator, timezone
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.views.decorators.csrf import csrf_protect

from nadine.models.profile import EmailAddress
from nadine import email

logger = logging.getLogger(__name__)

@login_required
def index(request):
    if request.user.is_staff:
        return HttpResponseRedirect(reverse('staff:home'))
    return HttpResponseRedirect(reverse('member:home'))


@csrf_protect
def password_reset(request, is_admin_site=False, template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', password_reset_form=PasswordResetForm, token_generator=default_token_generator, post_reset_redirect=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    if request.method == 'GET' and request.GET.get('email', None):
        form = password_reset_form(initial={'email': request.GET.get('email')})
    elif request.method == "POST":
        email = request.POST.get('email')
        valid = EmailAddress.objects.filter(email=email)
        if len(valid) > 0:
            logger.info("Resetting password for '%s'" % email)
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
            print('There is no user associated with that email. Please try again.')
            messages.error(request, 'There is no user associated with that email.')
            return render(request, template_name, {'form': password_reset_form()})
    else:
        form = password_reset_form()
    return render(request, template_name, {'form': form})


@login_required
def email_manage(request, email_pk, action):
    """Set the requested email address as the primary. Can only be
    requested by the owner of the email address."""
    email_address = get_object_or_404(EmailAddress, pk=email_pk)
    if not email_address.user == request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to manage this email address")
    # if not email_address.is_verified():
    #     messages.error(request, "Email '%s' needs to be verified first." % email_address.email)

    if action == "set_primary":
        email_address.set_primary()
        messages.success(request, "'%s' is now marked as your primary email address." % email_address.email)
    elif action == "delete":
        email_address.delete()
        messages.success(request, "'%s' has been removed." % email_address.email)

    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect(reverse('member:profile:view', kwargs={'username': email_address.user.username}))


@login_required
def email_add(request):
    user = get_object_or_404(User, username=request.POST.get("username"))
    email = request.POST.get("email")
    if email:
        e = EmailAddress(user=user, email=email.lower())
        e.save(verify=True)
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect(reverse('member:profile:view', kwargs={'username': email_address.user.username}))


@login_required
def email_delete(request, email_pk):
    """Delete the given email. Must be owned by current user."""
    email = get_object_or_404(EmailAddress, pk=int(email_pk))
    if email.user == request.user:
        if not email.is_verified():
            email.delete()
        else:
            num_verified_emails = len(request.user.emailaddress_set.filter(
                verified_at__isnull=False))
            if num_verified_emails > 1:
                email.delete()
            elif num_verified_emails == 1:
                if MM.ALLOW_REMOVE_LAST_VERIFIED_EMAIL:
                    email.delete()
                else:
                    messages.error(request,
                        MM.REMOVE_LAST_VERIFIED_EMAIL_ATTEMPT_MSG,
                            extra_tags='alert-error')
    else:
        messages.error(request, 'Invalid request.')
    return redirect(MM.DELETE_EMAIL_REDIRECT)


@csrf_protect
def email_verify(request, email_pk):
    email_address = get_object_or_404(EmailAddress, pk=email_pk)
    if email_address.is_verified():
        messages.error(request, "Email address was already verified.")
    if not email_address.user == request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to verify this email address")

    # Send the verification link if that was requested
    if 'send_link' in request.GET:
        email.send_verification(email_address)

    verif_key = request.GET.get('verif_key', "").strip()
    if len(verif_key) != 0:
        if email_address.verif_key == verif_key:
            # Looks good!  Mark as verified
            email_address.remote_addr = request.META.get('REMOTE_ADDR')
            email_address.remote_host = request.META.get('REMOTE_HOST')
            email_address.verified_ts = timezone.now()
            email_address.save()
            messages.success(request, "Email address has been verified.")
            return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': email_address.user.username}))
        else:
            messages.error(request, "Invalid Key")

    return render(request, "email_verify.html", {'email':email_address.email})


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
