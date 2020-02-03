import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone

from member.models import UserNotification
from nadine import email


class Command(BaseCommand):
    help = "Send User Notification Emails."

    def handle(self, *args, **options):
        here_today = list(User.helper.here_today())
        for n in UserNotification.objects.filter(sent_date__isnull=True):
            if n.notify_user in here_today:
                if n.target_user in here_today:
                    email.send_user_notifications(n.notify_user, n.target_user)
                    n.sent_date = timezone.localtime(timezone.now())
                    n.save()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
