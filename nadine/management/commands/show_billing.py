import os
import time
import urllib
from datetime import datetime, timedelta, date
import sys
import tempfile
import shutil
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


class Command(BaseCommand):
    help = "Shows the billing information for a given user."
    args = "[username]"
    requires_system_checks = False

    def handle(self, *args, **options):
        from staff.billing import Run
        if not args or len(args) != 1:
            raise CommandError('Enter one argument, a username.')
        username = int(args[0])
        try:
            user = User.objects.get(username=username)
            start_date = timezone.localtime(timezone.now()) - timedelta(days=365)
            end_date = timezone.localtime(timezone.now())
            print('Run info for %s (%s - %s)' % (user, start_date, end_date))
            run = Run(user, start_date, end_date, False)
            run.print_info()
        except:
            traceback.print_exc()
            print("Could not find user with username %s" % username)

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
