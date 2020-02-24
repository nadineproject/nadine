import traceback
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.conf import settings
from django.core import management
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now

from nadine.models import *

today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)
one_year_ago = today - relativedelta(years=1)


class AlertTestCase(TestCase):

    def setUp(self):
        pass

    def test_stale_member(self):
        # Start with a membership from a long time ago.
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        subscription = ResourceSubscription.objects.create(
            membership = user.membership,
            resource = Resource.objects.day_resource,
            start_date = one_year_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        self.assertFalse(MemberAlert.STALE_MEMBER in user.profile.alerts_by_key())

        # Trigger the period check and we should see this membership is stale
        MemberAlert.objects.handle_periodic_check()
        self.assertTrue(MemberAlert.STALE_MEMBER in user.profile.alerts_by_key(include_resolved=False))

        # Create a recent CoworkingDay and the membership is no longer stale
        CoworkingDay.objects.create(user=user, visit_date=yesterday)
        self.assertFalse(MemberAlert.STALE_MEMBER in user.profile.alerts_by_key(include_resolved=False))

    def test_new_key(self):
        # First user has no files and thus a new key subscription triggers KEY_AGREEMENT
        user1 = User.objects.create(username='test_one', first_name='Test', last_name='One')
        self.assertTrue(user1.profile.alerts().count() == 0)
        self.assertFalse(user1.profile.has_file(FileUpload.KEY_AGMT))
        ResourceSubscription.objects.create(
            membership = user1.membership,
            resource = Resource.objects.key_resource,
            start_date = today,
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        self.assertTrue(MemberAlert.KEY_AGREEMENT in user1.profile.alerts_by_key(include_resolved=False))

        # Second user has a key agreement on file and an open RETURN_DOOR_KEY
        user2 = User.objects.create(username='test_two', first_name='Test', last_name='Two')
        MemberAlert.objects.create(user=user2, key=MemberAlert.RETURN_DOOR_KEY)
        self.assertTrue(MemberAlert.RETURN_DOOR_KEY in user2.profile.alerts_by_key(include_resolved=False))
        FileUpload.objects.create(user=user2, document_type=FileUpload.KEY_AGMT, name="Key Agreement", uploaded_by=user2)
        self.assertTrue(user2.profile.has_file(FileUpload.KEY_AGMT))
        ResourceSubscription.objects.create(
            membership = user2.membership,
            resource = Resource.objects.key_resource,
            start_date = today,
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        # A new key subscription should not trigger a KEY_AGREEMENT
        # and it should resolve the open RETURN_DOOR_KEY
        self.assertFalse(MemberAlert.KEY_AGREEMENT in user2.profile.alerts_by_key(include_resolved=False))
        self.assertFalse(MemberAlert.RETURN_DOOR_KEY in user2.profile.alerts_by_key(include_resolved=False))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
