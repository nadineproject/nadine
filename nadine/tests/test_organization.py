import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import localtime, now

from nadine.models.organization import Organization


today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
last_month = today - timedelta(days=30)
next_month = today + timedelta(days=30)


class OrganiztionTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='user_one', first_name='User', last_name='One')
        self.user2 = User.objects.create(username='user_two', first_name='User', last_name='Two')

        self.org1 = Organization.objects.create(name="Organization One", lead=self.user1, created_by=self.user1)
        self.org2 = Organization.objects.create(name="Organization Two", lead=self.user2, created_by=self.user2)

        # User1 is a member of Org1 from today onward
        self.mem1 = self.org1.add_member(self.user1)

        # User2 was a member of Org2 for the past month
        self.mem2 = self.org2.add_member(self.user2, start_date=last_month, end_date=yesterday)

    def test_has_member(self):
        # Org1
        self.assertTrue(self.org1.has_member(self.user1))
        self.assertFalse(self.org1.has_member(self.user1, target_date=yesterday))
        self.assertFalse(self.org1.has_member(self.user2))
        # Org2
        self.assertFalse(self.org2.has_member(self.user1))
        self.assertFalse(self.org2.has_member(self.user2))
        self.assertTrue(self.org2.has_member(self.user2, target_date=yesterday))
        self.assertFalse(self.org2.has_member(self.user1, target_date=yesterday))

    def test_is_active(self):
        # User1 is active today, but not yesterday.
        self.assertTrue(self.mem1.is_active())
        self.assertFalse(self.mem1.is_active(target_date=yesterday))
        # User2 is active yesterday, but not today.
        self.assertFalse(self.mem2.is_active())
        self.assertTrue(self.mem2.is_active(target_date=yesterday))

    def test_members(self):
        self.assertTrue(self.user1 in self.org1.members())
        self.assertFalse(self.user1 in self.org1.members(target_date=yesterday))
        self.assertFalse(self.user1 in self.org2.members())
        self.assertFalse(self.user2 in self.org2.members())
        self.assertTrue(self.user2 in self.org2.members(target_date=yesterday))

    def test_active_organizations(self):
        # User1
        active_orgs = self.user1.profile.active_organizations()
        self.assertTrue(len(active_orgs) > 0)
        self.assertTrue(self.org1 in active_orgs)
        self.assertFalse(self.org2 in active_orgs)
        # User2
        active_orgs = self.user2.profile.active_organizations()
        self.assertTrue(len(active_orgs) == 0)
        active_orgs = self.user2.profile.active_organizations(target_date=yesterday)
        self.assertTrue(len(active_orgs) > 0)
        self.assertTrue(self.org2 in active_orgs)

    def test_can_edit(self):
        # Start out unlocked, lead, not admin
        self.assertFalse(self.org1.locked)
        self.assertEqual(self.org1.lead, self.user1)
        self.assertFalse(self.mem1.admin)
        # Unlocked
        self.assertTrue(self.org1.can_edit(self.user1))
        self.assertFalse(self.org1.can_edit(self.user2))
        # Locked & Lead
        self.org1.lock()
        self.assertTrue(self.org1.locked)
        self.assertTrue(self.org1.can_edit(self.user1))
        self.assertFalse(self.org1.can_edit(self.user2))
        # Locked & Not Lead & Not Admin
        self.org1.set_lead(self.user2)
        self.assertFalse(self.org1.can_edit(self.user1))
        # Locked & Admin
        self.mem1.set_admin(True)
        self.assertTrue(self.org1.can_edit(self.user1))

    def test_for_user(self):
        # User1 is a member today, but wasn't yesterday
        self.assertFalse(self.org1 in Organization.objects.for_user(self.user1, target_date=last_month))
        self.assertFalse(self.org1 in Organization.objects.for_user(self.user1, target_date=yesterday))
        self.assertTrue(self.org1 in Organization.objects.for_user(self.user1, target_date=today))
        self.assertTrue(self.org1 in Organization.objects.for_user(self.user1, target_date=tomorrow))
        self.assertTrue(self.org1 in Organization.objects.for_user(self.user1, target_date=next_month))
        # User2 was a member yesterday but not today
        self.assertTrue(self.org2 in Organization.objects.for_user(self.user2, target_date=last_month))
        self.assertTrue(self.org2 in Organization.objects.for_user(self.user2, target_date=yesterday))
        self.assertFalse(self.org2 in Organization.objects.for_user(self.user2, target_date=today))
        self.assertFalse(self.org2 in Organization.objects.for_user(self.user2, target_date=tomorrow))
        self.assertFalse(self.org2 in Organization.objects.for_user(self.user2, target_date=next_month))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
