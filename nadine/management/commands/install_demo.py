import os
import sys
import time
import urllib.request, urllib.parse, urllib.error
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from nadine.models.core import Industry, Neighborhood
from nadine.models.profile import UserProfile
from nadine.models.membership import MembershipPlan, Membership
from nadine.models.usage import CoworkingDay
from nadine.models.payment import BillingLog, Bill, Transaction
from interlink.models import MailingList, IncomingMail, OutgoingMail


class Command(BaseCommand):
    help = "Destructively resets the database and installs some demonstration data."
    args = ""
    requires_system_checks = True

    def handle(self, *args, **options):
        if settings.PRODUCTION:
            raise Exception('Will not install the demo on production.')

        self.delete_all(BillingLog)
        self.delete_all(Bill)
        self.delete_all(Transaction)
        self.delete_all(CoworkingDay)
        self.delete_all(MembershipPlan)
        self.delete_all(Membership)
        self.delete_all(UserProfile)
        self.delete_all(User)
        self.delete_all(Industry)
        self.delete_all(Neighborhood)
        self.delete_all(IncomingMail)
        self.delete_all(OutgoingMail)
        self.delete_all(MailingList)

        call_command('syncdb', interactive=False)
        call_command('migrate', interactive=False)

        site = Site.objects.get_current()
        site.domain = '127.0.0.1:8000'
        site.name = 'Nadine'
        site.save()

        basic_plan = MembershipPlan.objects.create(name='Basic', description='An occasional user', monthly_rate='50', daily_rate='25', dropin_allowance='5')
        resident_plan = MembershipPlan.objects.create(name='Resident', description='A frequent user', monthly_rate='500', daily_rate='20', has_desk=True)

        knitters_ml = MailingList.objects.create(name='Knitters', description='Knitters of the space', email_address='knitters@example.com', username='knitters', password='1234', pop_host='pop.example.com', smtp_host='smtp.example.com', )
        gamers_ml = MailingList.objects.create(name='Game players', description='People who play board games', email_address='gamers@example.com', username='gamers', password='1234', pop_host='pop.example.com', smtp_host='smtp.example.com', )

        alice = self.create_user('alice', '1234', 'Alice', 'Templeton', is_staff=True, is_superuser=True, email='alice@example.com')
        knitters_ml.moderators.add(alice)

        terry = self.create_user('terry', '1234', 'Terry', 'Moofty', email='terry@example.com')
        Membership.objects.create(user=terry, membership_plan=resident_plan, start_date=timezone.now().date() - timedelta(days=400), daily_rate=0, has_desk=True)
        knitters_ml.subscribers.add(terry)

        bob = self.create_user('bob', '1234', 'Bob', 'Stilton', email='bob@example.com')
        Membership.objects.create(user=bob, membership_plan=basic_plan, start_date=timezone.now().date() - timedelta(days=92), daily_rate=25)
        knitters_ml.subscribers.add(bob)

    def delete_all(self, cls):
        for item in cls.objects.all():
            item.delete()

    def create_user(self, username, password, first_name=None, last_name=None, location=None, is_staff=False, is_superuser=False, email=None):
        user, created = User.objects.get_or_create(username=username, first_name=first_name, last_name=last_name, is_staff=is_staff, is_superuser=is_superuser, email=email)
        user.set_password(password)
        user.save()
        return user

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
