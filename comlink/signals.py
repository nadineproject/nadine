# -*- coding: utf-8 -*-
import logging

from django.dispatch import Signal, receiver
from django.contrib.auth.models import User
from django.conf import settings

from comlink import mailgun
from comlink.models import MailingList


logger = logging.getLogger(__name__)

email_received = Signal(providing_args=["instance", "attachments"])

@receiver(email_received)
def router(sender, **kwargs):
    # Pull our email object and convert it to the mailgun_data we need`
    email = kwargs['instance']
    strip_emails = getattr(settings, "COMLINK_STRIP_EMAILS", False)
    mailgun_data = email.get_mailgun_data(stripped=strip_emails)
    logger.debug("In Router: ")
    logger.debug(mailgun_data)

    # Pull our attachments and convert it to the list of files we need
    attachments = kwargs['attachments']
    files = []
    for a in attachments:
        files.append(('attachment', open(a.file.path, mode='rb')))

    # Build out the BCC depending on who the recipient is
    bcc_list = None
    mailing_list = MailingList.objects.filter(address=email.recipient).first()
    if mailing_list:
        mailing_list.emailmessage_set.add(email)
        if mailing_list.is_members_only:
            if not mailing_list.is_subscriber(email.from_address):
                raise mailgun.MailgunException("Members Only Mailing List '%s' received email from non-member '%s'" % (mailing_list.name, email.from_address))
        bcc_list = mailing_list.subscriber_addresses
        mailgun.inject_footer(mailgun_data, mailing_list.unsubscribe_url)
        if mailing_list.subject_prefix and mailing_list.subject_prefix not in mailgun_data["subject"]:
            mailgun_data["subject"] = ' '.join((mailing_list.subject_prefix, mailgun_data["subject"]))
    elif hasattr(settings, "STAFF_EMAIL_ADDRESS") and settings.STAFF_EMAIL_ADDRESS in email.recipient:
        bcc_list = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
        mailgun.inject_footer(mailgun_data, email.public_url)
    elif hasattr(settings, "TEAM_EMAIL_ADDRESS") and settings.TEAM_EMAIL_ADDRESS in email.recipient:
        bcc_list = list(User.helper.managers(include_future=True).values_list('email', flat=True))
        mailgun.inject_footer(mailgun_data, email.public_url)
    logger.debug("BCC List:")
    logger.debug(bcc_list)

    if bcc_list:
        # Pass this message along
        mailgun_data["bcc"] = bcc_list
        mailgun.mailgun_send(mailgun_data, files)


# Copyright 2020 The Nadine Project (https://nadineproject.org/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
