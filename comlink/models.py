# -*- coding: utf-8 -*-
import json
import logging

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.contrib.sites.models import Site

from email.utils import parseaddr

UPLOAD_TO = getattr(settings, "COMLINK_UPLOAD_TO", "attachments/")

logger = logging.getLogger(__name__)


class EmailBaseModel(models.Model):
    sender = models.EmailField(_("sender"), max_length=255)
    from_str = models.CharField(_("from"), max_length=255)
    recipient = models.CharField(_("recipient"), max_length=255)
    subject = models.CharField(_("subject"), max_length=255, blank=True)
    body_plain = models.TextField(_("body plain"), blank=True)
    body_html = models.TextField(_("body html"), blank=True)
    stripped_text = models.TextField(_("stripped text"), blank=True)
    stripped_html = models.TextField(_("stripped html"), blank=True)
    stripped_signature = models.TextField(_("stripped signature"), blank=True)
    message_headers = models.TextField(_("message headers"), blank=True, help_text=_("Stored in JSON."))
    content_id_map = models.TextField(_("Content-ID map"), blank=True, help_text=_("Dictionary mapping Content-ID (CID) values to corresponding attachments. Stored in JSON."))
    received = models.DateTimeField(_("received"), auto_now_add=True)

    class Meta:
        abstract = True
        verbose_name = _("incoming email")
        verbose_name_plural = _("incoming emails")

    def __init__(self, *args, **kwargs):
        super(EmailBaseModel, self).__init__(*args, **kwargs)
        self._headers = None
        self._cids = None

    def _load_headers(self):
        self._headers = MultiValueDict()
        try:
            header_list = json.loads(self.message_headers)
            for key, val in header_list:
                self._headers.appendlist(key, val)
        except:
            logger.exception("Error parsing JSON data containing message headers")

    @property
    def headers(self):
        """Access message_headers parsed into MultiValueDict"""
        if self._headers is None:
            self._load_headers()
        return self._headers

    def _load_cids(self):
        if self.content_id_map:
            self._cids = {}
        try:
            self._cids = json.loads(self.content_id_map)
        except:
            logger.exception("Error parsing JSON data containing Content-IDs")

    @property
    def content_ids(self):
        """Access content_id_map as dict"""
        if not self.content_id_map:
            return
        if self._cids is None:
            self._load_cids()
        return self._cids

    @property
    def message_id(self):
        return self.headers.get('Message-Id', None)

    @property
    def cc(self):
        return self.headers.get('Cc', None)

    @property
    def references(self):
        return self.headers.get('References', None)

    @property
    def in_reply_to(self):
        return self.headers.get('In-Reply-To', None)

    @property
    def site_url(self): return 'https://%s%s' % (Site.objects.get_current().domain, reverse('comlink:mail', kwargs={'id': self.id}))

    def get_mailgun_data(self, stripped=True, footer=True):
        if stripped:
            body_plain = self.stripped_text
            body_html = self.stripped_html
        else:
            body_plain = self.body_plain
            body_html = self.body_html

        if footer:
            # Add in a footer
            text_footer = "\n\n-------------------------------------------\n*~*~*~* Sent through Nadine *~*~*~*\n%s" % self.site_url
            body_plain = body_plain + text_footer
            if body_html:
                html_footer = "<br><br>-------------------------------------------<br>*~*~*~* Sent through Nadine *~*~*~*\n%s" % self.site_url
                body_html = body_html + html_footer

        # Build and return our data
        mailgun_data = {"from": self.from_str,
                        "to": [self.recipient, ],
                        "cc": [self.cc, ],
                        "subject": self.subject,
                        "text": body_plain,
                        "html": body_html,
                        }
        return mailgun_data

    def __str__(self):
        return _("Message from {from_str}: {subject_trunc}").format(
            from_str=self.from_str,
            subject_trunc=self.subject[:20])


class IncomingEmail(EmailBaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_("user"), on_delete=models.CASCADE)


class Attachment(models.Model):
    email = models.ForeignKey(IncomingEmail, verbose_name=_("email"), on_delete=models.CASCADE)
    file = models.FileField(_("file"), upload_to=UPLOAD_TO)
    content_id = models.CharField(_("Content-ID"), max_length=255, blank=True,
                                  help_text=_("Content-ID (CID) referencing this attachment."))

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    def __str__(self):
        if self.file:
            return self.file.name
        return "(no file)"


class SimpleMailingList(models.Model):
    name = models.CharField(max_length=128)
    address = models.EmailField(unique=True)
    subscribers = models.ManyToManyField(User, blank=True, related_name='simple_mailing_lists')
    access_ts = models.DateTimeField(auto_now=True)

    def get_subscriber_list(self):
        emails = []
        for u in self.subscribers.all():
            emails.append(u.email)
        return emails


# Copyright 2018 The Nadine Project (http://nadineproject.org/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
