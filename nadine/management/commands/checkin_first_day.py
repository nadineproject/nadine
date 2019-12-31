from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.usage import CoworkingDay
from nadine import email


class Command(BaseCommand):
    help = "Check-in with users after their first day"

    def handle(self, *args, **options):
        today = localtime(now()).date()
        free_trials_today = CoworkingDay.objects.filter(visit_date=today, payment='Trial')
        for d in free_trials_today:
            email.send_first_day_checkin(d.user)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
