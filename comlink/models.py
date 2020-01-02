# -*- coding: utf-8 -*-
import json
import logging
import email.utils

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ugettext as _
from django.urls import reverse

from email.utils import parseaddr

UPLOAD_TO = getattr(settings, "COMLINK_UPLOAD_TO", "attachments/")

logger = logging.getLogger(__name__)


class MailingList(models.Model):
    name = models.CharField(max_length=128)
    subject_prefix = models.CharField(max_length=64, blank=True)
    address = models.EmailField(unique=True)
    access_ts = models.DateTimeField(auto_now=True)
    is_members_only = models.BooleanField(default=True)
    is_opt_out = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True, help_text='Set to False to disable this list.')
    subscribers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='+', blank=True)
    unsubscribed = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='+', blank=True)
    moderators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='+', blank=True, limit_choices_to={'is_staff': True})

    @property
    def unsubscribe_url(self):
        # TODO - Make this a link to unsubscribe from this mailing list
        return settings.SITE_PROTO + "://" + settings.SITE_DOMAIN

    @property
    def subscriber_addresses(self):
        return list(self.subscribed().values_list('email', flat=True))

    def subscribed(self):
        """ The subscribers minus the unsubscriberd. """
        return self.subscribers.exclude(id__in=self.unsubscribed.all())

    def is_subscriber(self, email):
        user = User.helper.by_email(email)
        return user in self.subscribers.all()

    def subscribe(self, user):
        """ Subscribe the given user to this mailing list. """
        self.subscribers.add(user)
        self.unsubscribed.remove(user)

    def unsubscribe(self, user):
        """ Unsubscribe the given user to this mailing list. """
        self.subscribers.remove(user)
        self.unsubscribed.add(user)


    def __str__(self):
        return '%s' % self.name


class EmailMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_("user"), on_delete=models.SET_NULL)
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
    mailing_list = models.ForeignKey(MailingList, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("email message")
        verbose_name_plural = _("email messages")

    def __init__(self, *args, **kwargs):
        super(EmailMessage, self).__init__(*args, **kwargs)
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

    def _load_cids(self):
        if self.content_id_map:
            self._cids = {}
        try:
            self._cids = json.loads(self.content_id_map)
        except:
            logger.exception("Error parsing JSON data containing Content-IDs")

    @property
    def headers(self):
        """Access message_headers parsed into MultiValueDict"""
        if self._headers is None:
            self._load_headers()
        return self._headers

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
    def from_name(self):
        from_name, from_address = email.utils.parseaddr(self.from_str)
        return from_name

    @property
    def from_address(self):
        from_name, from_address = email.utils.parseaddr(self.from_str)
        return from_address

    @property
    def clean_subject(self):
        subject = self.subject
        if self.mailing_list and self.mailing_list.subject_prefix:
            prefix = self.mailing_list.subject_prefix
            index = subject.find(prefix)
            if index >= 0:
                subject = subject[index + len(prefix):]
        return subject.strip()

    @property
    def is_moderated_subject(self):
        s = self.subject.lower()
        if "auto-reply" in s:
            return True
        if "auto reply" in s:
            return True
        if "automatic reply" in s:
            return True
        if "out of office" in s:
            return True
        return False

    @property
    def public_url(self):
        return settings.SITE_PROTO + "://" + settings.SITE_DOMAIN + reverse('comlink:mail', kwargs={'id': self.id})

    def get_user(self):
        if not self.user:
            self.user = User.helper.by_email(self.from_address)
        return self.user

    def get_body(self, prefer_html=True):
        if prefer_html:
            if self.stripped_html:
                return self.stripped_html
            if self.body_html:
                return self.body_html
        if self.stripped_text:
            return self.stripped_text
        return self.body_plain

    def get_mailgun_data(self, stripped=True):
        if stripped:
            body_plain = self.stripped_text
            body_html = self.stripped_html
        else:
            body_plain = self.body_plain
            body_html = self.body_html

        # Build and return our data
        mailgun_data = {
            "from": self.from_str,
            "to": [self.recipient, ],
            "cc": [self.cc, ],
            "subject": self.clean_subject,
            "text": body_plain,
            "html": body_html,
        }
        return mailgun_data

    def __str__(self):
        return _("Message from {from_str}: {subject_trunc}").format(
            from_str=self.from_str,
            subject_trunc=self.subject[:20]
        )


class Attachment(models.Model):
    attached_to = models.ForeignKey(EmailMessage, related_name="attachments", on_delete=models.CASCADE)
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


# Copyright 2020 The Nadine Project (https://nadineproject.org/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
