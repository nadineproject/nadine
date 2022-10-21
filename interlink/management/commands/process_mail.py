import sys
import urllib.request, urllib.parse, urllib.error
import logging
import datetime

logger = logging.getLogger()

from django.core.management.base import BaseCommand, CommandError

from interlink.models import MailingList, IncomingMail, OutgoingMail


class Command(BaseCommand):
    help = "Process all the mail from our MailingLists"

    def handle(self, *args, **options):
        # MailingList.objects.fetch_all_mail(logger)
        MailingList.objects.fetch_all_mail()
        IncomingMail.objects.process_incoming()
        OutgoingMail.objects.send_outgoing()


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

