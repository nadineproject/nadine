# -*- coding: utf-8 -*-
import hashlib
import hmac
import logging

from django.conf import settings
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from comlink.forms import EmailForm
from comlink.models import Attachment, IncomingEmail
from comlink.signals import email_received
from comlink.exceptions import RejectedMailException

logger = logging.getLogger(__name__)

API_KEY = getattr(settings, "MAILGUN_API_KEY", "")

VERIFY_SIGNATURE = getattr(settings, "MAILGUN_VERIFY_INCOMING", not settings.DEBUG)


class Incoming(View):
    email_model = IncomingEmail
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
        print(request.POST)

        if self.verify:
            verified = self.verify_signature(request.POST.get('token', ''),
                                             request.POST.get('timestamp', ''),
                                             request.POST.get('signature', ''))
            if not verified:
                logger.debug("Signature verification failed.")
                return HttpResponseBadRequest("Invalid signature")

        form = self.get_form()(request.POST)
        email = form.save()

        attachments = []
        if form.cleaned_data.get('attachment-count', False):

            # reverse mapping in content_ids dict
            content_ids = dict(
                (attnr, cid) for cid, attnr in
                (email.content_ids or {}).iteritems())

            i = 1
            for file in request.FILES.values():
                attachment = self.attachment_model(email=email,
                    file=file,
                    content_id=content_ids.get('attachment-{0!s}'.format(i), ''))
                attachment.save()

                attachments.append(attachment)
                i = i + 1

        # See if any attached signal handlers throw an error
        try:
            self.handle_email(email, attachments=attachments)
            return HttpResponse("OK")
        except RejectedMailException, e:
            return HttpResponse("Email not accepted", status=406)

    def handle_email(self, email, attachments=None):
        email_received.send(
            sender=self.email_model, instance=email, attachments=attachments or [])

    def verify_signature(self, token, timestamp, signature):
        return signature == hmac.new(key=self.api_key,
                                     msg='{0}{1}'.format(timestamp, token),
                                     digestmod=hashlib.sha256).hexdigest()
