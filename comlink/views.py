# -*- coding: utf-8 -*-
import hmac
import hashlib
import logging

from django.conf import settings
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from comlink.forms import EmailForm
from comlink.models import Attachment, EmailMessage, MailingList
from comlink.signals import email_received
from comlink.exceptions import RejectedMailException, DroppedMailException
from comlink import jwzthreading

logger = logging.getLogger(__name__)

API_KEY = getattr(settings, "MAILGUN_API_KEY", "")

VERIFY_SIGNATURE = getattr(settings, "COMLINK_VERIFY_INCOMING", not settings.DEBUG)


##########################################################################
# User Interface Views
##########################################################################


@staff_member_required
def home(request):
    # messages = EmailMessage.objects.all().order_by("-received")
    # threads = jwzthreading.thread(messages)
    inboxes = []
    for a in MailingList.objects.all().values('address'):
        inboxes.append({'address': a})
    if hasattr(settings, "STAFF_EMAIL_ADDRESS"):
        inboxes.append({'address': settings.STAFF_EMAIL_ADDRESS})
    if hasattr(settings, "TEAM_EMAIL_ADDRESS"):
        inboxes.append({'address': settings.TEAM_EMAIL_ADDRESS})
    for i in inboxes:
        c = EmailMessage.objects.filter(recipient__contains=i['address']).count()
        i['messages'] = c
    # context = {'messages':messages, 'inboxes':inboxes}
    context = {'inboxes':inboxes}
    return render(request, 'comlink/home.html', context)


@staff_member_required
def inbox(request, address):
    # TODO - make sure they are able to read this email
    messages = EmailMessage.objects.filter(recipient__contains=address).order_by("-received")
    context = {'messages':messages, 'address':address}
    return render(request, 'comlink/inbox.html', context)


@staff_member_required
def view_mail(request, id):
    message = get_object_or_404(EmailMessage, id=id)
    headers = message.headers
    context = {'message':message, 'headers':headers}
    return render(request, 'comlink/mail.html', context)


##########################################################################
# Incoming Mail Views
##########################################################################


class Incoming(View):
    email_model = EmailMessage
    attachment_model = Attachment
    form = EmailForm
    api_key = API_KEY
    verify = VERIFY_SIGNATURE

    def get_form(self):
        return modelform_factory(self.email_model, form=self.form, exclude=[])

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Incoming, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        logger.info("Incoming email")
        logger.debug("POST: %s" % request.POST)
        if self.verify:
            logger.debug("Verifying Signature")
            verified = self.verify_signature(request.POST.get('token', ''),
                                             request.POST.get('timestamp', ''),
                                             request.POST.get('signature', ''))
            if not verified:
                logger.debug("Signature verification failed.")
                return HttpResponseBadRequest("Invalid signature")

        try:
            form = self.get_form()(request.POST)
            email = form.save()
        except DroppedMailException:
            # This is because we got a ListID or something. It's OK.
            logger.debug("Quietly dropping the message")
            return HttpResponse("OK")

        # Try to link the sender to a user
        user = User.helper.by_email(email.sender)
        if user:
            email.user = user
            email.save()

        attachments = []
        if form.cleaned_data.get('attachment-count', False):
            # reverse mapping in content_ids dict
            content_ids = dict(
                (attnr, cid) for cid, attnr in
                (email.content_ids or {}).items())

            i = 1
            for file in list(request.FILES.values()):
                attachment = self.attachment_model(
                    attached_to=email,
                    file=file,
                    content_id=content_ids.get('attachment-{0!s}'.format(i), ''))
                attachment.save()
                attachments.append(attachment)
                i = i + 1

        # See if any attached signal handlers throw an error
        try:
            email_received.send(sender=self.email_model, instance=email, attachments=attachments or [])
            return HttpResponse("OK")
        except RejectedMailException as e:
            logger.debug("Email was rejected: %s" % str(e))
            return HttpResponse("Email not accepted", status=406)

    def verify_signature(self, token, timestamp, signature):
        # logger.debug("token=%s, timestamp=%s, signature=%s" % (token, timestamp, signature))
        byte_key = bytes(self.api_key.encode("utf-8"))
        formatted_msg = '{0}{1}'.format(timestamp, token).encode("utf-8")
        hashed_signature = hmac.new(key=byte_key, msg=formatted_msg, digestmod=hashlib.sha256)
        verified = signature == hashed_signature.hexdigest()
        logger.debug("signature verified = %s" % verified)
        return verified


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
