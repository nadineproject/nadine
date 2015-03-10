import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import staff.billing as billing
from interlink.models import MailingList
from staff.views import beginning_of_next_month, first_days_in_months
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
        Membership.objects.create(member=self.user1.get_profile(), membership_plan=self.basicPlan, start_date=date(2008, 2, 26), end_date=date(2010, 6, 25))
        Membership.objects.create(member=self.user1.get_profile(), membership_plan=self.residentPlan, start_date=date(2010, 6, 26))

        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.profile2 = self.user2.profile
        Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1))

        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.profile3 = self.user3.profile
        self.profile3.neighborhood = self.neighborhood1
        self.profile3.save()
        self.user3.profile.save()

        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        self.profile4 = self.user4.profile
        self.profile4.neighborhood = self.neighborhood1
        self.profile4.save()
        Membership.objects.create(member=self.user4.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), end_date=date(2010, 1, 1))

        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        self.profile5 = self.user5.profile
        self.profile5.valid_billing = False
        self.profile5.save()
        Membership.objects.create(member=self.user5.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), guest_of=self.profile1)

    def test_info_methods(self):
        self.assertTrue(self.user1.profile in Member.objects.members_by_plan_id(self.residentPlan.id))
        self.assertFalse(self.user1.profile in Member.objects.members_by_plan_id(self.basicPlan.id))
        self.assertTrue(self.user2.profile in Member.objects.members_by_plan_id(self.pt5Plan.id))
        self.assertFalse(self.user2.profile in Member.objects.members_by_plan_id(self.residentPlan.id))

        self.assertTrue(self.user1.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user2.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
        self.assertTrue(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))
        self.assertTrue(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))

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
        self.assertEquals(self.user5.profile.is_guest(), self.user1.profile)

    def test_tags(self):
        member1 = self.user1.get_profile()
        member1.tags.add("coworking", "books", "beer")
        member2 = self.user2.get_profile()
        member2.tags.add("beer", "cars", "women")
        member3 = self.user3.get_profile()
        member3.tags.add("knitting", "beer", "travel")
        self.assertTrue(member1 in Member.objects.filter(tags__name__in=["beer"]))
        self.assertTrue(member2 in Member.objects.filter(tags__name__in=["beer"]))
        self.assertTrue(member3 in Member.objects.filter(tags__name__in=["beer"]))
        self.assertFalse(member1 in Member.objects.filter(tags__name__in=["knitting"]))
        self.assertFalse(member3 in Member.objects.filter(tags__name__in=["books"]))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
