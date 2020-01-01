import sys
import urllib.request, urllib.parse, urllib.error
import logging
import datetime

logger = logging.getLogger()

from django.core.management.base import BaseCommand, CommandError

from interlink import models as il_models
from comlink import models as cl_models

class Command(BaseCommand):
    requires_system_checks = True

    def handle(self, *args, **options):
        print("Moving Mailing Lists...")
        for old_list in il_models.MailingList.objects.all():
            new_list = cl_models.MailingList.objects.filter(name=old_list.name).first()
            if not new_list:
                print("    Creating List '%s'" % old_list.name)
                new_list = cl_models.MailingList.objects.create (
                    name = old_list.name,
                    subject_prefix = old_list.subject_prefix,
                    address = old_list.email_address,
                    is_members_only = True,
                    is_opt_out = old_list.is_opt_out,
                    enabled = old_list.enabled,
                )

                print("    Adding Subcribers and Unsubscribed...")
                for u in old_list.subscribers.all():
                    new_list.subscribers.add(u)
                for u in old_list.unsubscribed.all():
                    new_list.unsubscribed.add(u)
                for u in old_list.moderators.all():
                    new_list.moderators.add(u)

                print("    Moving Emails...")
                for old_msg in old_list.incoming_mails.all():
                    if not old_msg.body and not old_msg.html_body:
                        print("! Found Empty Email: %s" % old_msg.subject)
                        continue
                    text_body = old_msg.body
                    if not text_body:
                        text_body = ""
                    html_body = old_msg.html_body
                    if not html_body:
                        html_body = old_msg.body
                    new_msg = cl_models.EmailMessage.objects.create(
                        mailing_list = new_list,
                        user = old_msg.owner,
                        received = old_msg.sent_time,
                        sender = old_msg.origin_address,
                        from_str = old_msg.origin_address,
                        recipient = old_list.email_address,
                        subject = old_msg.subject[:255],
                        body_plain = text_body,
                        body_html = html_body,
                        # stripped_signature,
                        # message_headers,
                        # content_id_map,
                    )



# Copyright 2020 Office Nomads LLC (https://officenomads.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
