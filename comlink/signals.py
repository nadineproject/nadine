# -*- coding: utf-8 -*-
import logging

from django.dispatch import Signal, receiver
from django.contrib.auth.models import User
from django.conf import settings

from nadine.utils import mailgun
from comlink.models import SimpleMailingList

logger = logging.getLogger(__name__)

email_received = Signal(providing_args=["instance", "attachments"])


@receiver(email_received)
def router(sender, **kwargs):
    # Pull our email object and convert it to the mailgun_data we need`
    email = kwargs['instance']
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)
    logger.debug("In Router: ")
    logger.debug(mailgun_data)

    # Pull our attachments and convert it to the list of files we need
    attachments = kwargs['attachments']
    files = []
    for a in attachments:
        files.append(('attachment', open(a.file.path)))

    # Build out the BCC depending on who the recipient is
    bcc_list = None
    mailing_list = SimpleMailingList.objects.filter(address=email.recipient).first()
    if mailing_list:
        bcc_list = mailing_list.get_subscriber_list()
    elif hasattr(settings, "STAFF_EMAIL_ADDRESS") and email.recipient == settings.STAFF_EMAIL_ADDRESS:
        bcc_list = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
    elif hasattr(settings, "TEAM_EMAIL_ADDRESS") and email.recipient == settings.TEAM_EMAIL_ADDRESS:
        bcc_list = list(User.helper.managers(include_future=True).values_list('email', flat=True))
    logger.debug("BCC List:")
    logger.debug(bcc_list)

    if bcc_list:
        # Pass this message along
        mailgun_data["bcc"] = bcc_list
        mailgun.mailgun_send(mailgun_data, files)


# Copyright 2017 The Nadine Project (http://nadineproject.org/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
