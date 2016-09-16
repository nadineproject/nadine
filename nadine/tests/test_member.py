import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from nadine.models import *


class MemberTestCase(TestCase):

    def setUp(self):
        self.neighborhood1 = Neighborhood.objects.create(name="Beggar's Gulch")
        self.basicPlan = MembershipPlan.objects.create(name="Basic", monthly_rate=50, dropin_allowance=3, daily_rate=20, has_desk=False)
        self.pt5Plan = MembershipPlan.objects.create(name="PT5", monthly_rate=75, dropin_allowance=5, daily_rate=20, has_desk=False)
        self.residentPlan = MembershipPlan.objects.create(name="Resident", monthly_rate=475, dropin_allowance=5, daily_rate=20, has_desk=True)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.profile1 = self.user1.profile
        self.profile1.neighborhood = self.neighborhood1
        self.profile1.valid_billing = True
        self.profile1.save()
        Membership.objects.create(user=self.user1, membership_plan=self.basicPlan, start_date=date(2008, 2, 26), end_date=date(2010, 6, 25))
        Membership.objects.create(user=self.user1, membership_plan=self.residentPlan, start_date=date(2010, 6, 26))

        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.profile2 = self.user2.profile
        Membership.objects.create(user=self.user2, membership_plan=self.pt5Plan, start_date=date(2009, 1, 1))

        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.profile3 = self.user3.profile
        self.profile3.neighborhood = self.neighborhood1
        self.profile3.save()
        self.user3.profile.save()

        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        self.profile4 = self.user4.profile
        self.profile4.neighborhood = self.neighborhood1
        self.profile4.save()
        Membership.objects.create(user=self.user4, membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), end_date=date(2010, 1, 1))

        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        self.profile5 = self.user5.profile
        self.profile5.valid_billing = False
        self.profile5.save()
        Membership.objects.create(user=self.user5, membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), paid_by=self.user1)

    def test_info_methods(self):
        self.assertTrue(self.user1 in User.helper.members_by_plan(self.residentPlan))
        self.assertFalse(self.user1 in User.helper.members_by_plan(self.basicPlan))
        self.assertTrue(self.user2 in User.helper.members_by_plan(self.pt5Plan))
        self.assertFalse(self.user2 in User.helper.members_by_plan(self.residentPlan))

        self.assertTrue(self.user1 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user2 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user3 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user4 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertTrue(self.user3 in User.helper.members_by_neighborhood(self.neighborhood1, active_only=False))
        self.assertTrue(self.user4 in User.helper.members_by_neighborhood(self.neighborhood1, active_only=False))

    def test_valid_billing(self):
        # Member 1 has valid billing
        self.assertTrue(self.user1.profile.valid_billing)
        self.assertTrue(self.user1.profile.has_valid_billing())
        # Member 2 does not have valid billing
        self.assertFalse(self.user2.profile.valid_billing)
        self.assertFalse(self.user2.profile.has_valid_billing())
        # Member 5 does not have valid billing but is a guest of Member 1
        self.assertFalse(self.user5.profile.valid_billing)
        self.assertTrue(self.user5.profile.has_valid_billing())
        self.assertEquals(self.user5.profile.is_guest(), self.user1)

    def test_tags(self):
        self.user1.profile.tags.add("coworking", "books", "beer")
        self.user2.profile.tags.add("beer", "cars", "women")
        self.user3.profile.tags.add("knitting", "beer", "travel")
        self.assertTrue(self.user1.profile in UserProfile.objects.filter(tags__name__in=["beer"]))
        self.assertTrue(self.user2.profile in UserProfile.objects.filter(tags__name__in=["beer"]))
        self.assertTrue(self.user3.profile in UserProfile.objects.filter(tags__name__in=["beer"]))
        self.assertFalse(self.user1.profile in UserProfile.objects.filter(tags__name__in=["knitting"]))
        self.assertFalse(self.user3.profile in UserProfile.objects.filter(tags__name__in=["books"]))

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
