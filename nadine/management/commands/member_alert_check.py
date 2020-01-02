from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.alerts import MemberAlert


class Command(BaseCommand):
    help = "Check for any MemberAlerts that need to go out"

    def handle(self, *args, **options):
        MemberAlert.objects.handle_periodic_check()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
