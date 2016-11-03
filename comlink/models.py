# -*- coding: utf-8 -*-
import json
import logging

from django.conf import settings
from django.db import models
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ugettext as _
from email.Utils import parseaddr

UPLOAD_TO = getattr(settings, "MAILGUN_UPLOAD_TO", "attachments/")

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
            logger.exception(
                "Error parsing JSON data containing message headers")

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
    def cc(self):
        return self.headers.get('Cc', None)

    def __unicode__(self):
        return _("Message from {from_str}: {subject_trunc}").format(
            from_str=self.from_str,
            subject_trunc=self.subject[:20])


class IncomingEmail(EmailBaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, verbose_name=_("user"))


class Attachment(models.Model):
    email = models.ForeignKey(IncomingEmail, verbose_name=_("email"))
    file = models.FileField(_("file"), upload_to=UPLOAD_TO)
    content_id = models.CharField(_("Content-ID"), max_length=255, blank=True,
                                  help_text=_("Content-ID (CID) referencing this attachment."))

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    def __unicode__(self):
        if self.file:
            return self.file.name
        return unicode(_("(no file)"))
