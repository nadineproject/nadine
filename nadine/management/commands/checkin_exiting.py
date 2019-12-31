from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.membership import ResourceSubscription
from nadine import email


class Command(BaseCommand):
    help = "Check-in with users who are leaving"

    def handle(self, *args, **options):
        # Send an exit survey to members that have been gone a week.
        today = localtime(now()).date()
        one_week_ago = today - relativedelta(weeks=1)
        print(("Checking for subscriptions ending: %s" % one_week_ago))
        for subscription in ResourceSubscription.objects.filter(end_date=one_week_ago):
            if not subscription.user.profile.is_active():
                print(("  Sending exit survey to %s" % subscription.user.get_full_name()))
                email.send_exit_survey(subscription.user)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
