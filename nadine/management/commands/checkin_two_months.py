from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.membership import Membership, ResourceSubscription
from nadine import email


class Command(BaseCommand):
    help = "Check-in with users after two months"

    def handle(self, *args, **options):
        # Pull the subscriptions that started 2 months ago and send a survey
        # if they are still active and this was their first membership
        today = localtime(now()).date()
        two_months_ago = today - relativedelta(months=2)
        print(("Checking for subscriptions starting on: %s" % two_months_ago))
        for subscription in ResourceSubscription.objects.filter(start_date=two_months_ago):
            user = subscription.user
            membership = Membership.objects.for_user(user)
            first_membership = ResourceSubscription.objects.filter(membership=membership, start_date__lt=two_months_ago).count() == 0
            is_active = user.profile.is_active(today)
            if first_membership and is_active:
                print(("  Sending membership survey to %s" % user.get_full_name()))
                email.send_member_survey(membership.user)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
