from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.membership import Membership
from nadine import email


class Command(BaseCommand):
    help = "Check-in with users who are leaving"

    def handle(*args, **options):
        # Send an exit survey to members that have been gone a week.
        today = localtime(now()).date()
        one_week_ago = today - relativedelta(weeks=1)
        for membership in Membership.objects.filter(end_date=one_week_ago):
            if not membership.user.profile.is_active():
                email.send_exit_survey(membership.user)


# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
