import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from nadine.models import *

class OrganiztionTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='user_one', first_name='User', last_name='One')
        self.org1 = Organization.objects.create(name="Organization One", lead=self.user1, created_by=self.user1)

    def test_add_member(self):
        self.assertFalse(self.org1.is_member(self.user1))
        m = self.org1.add_member(self.user1)
        self.assertTrue(self.org1.is_member(self.user1))
        self.assertTrue(m.is_active())
        self.assertTrue(self.user1 in self.org1.members())

    def test_is_member(self):
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_month = today - timedelta(days=30)
        m = self.org1.add_member(self.user1, start_date=last_month, end_date=yesterday)
        self.assertFalse(self.org1.is_member(self.user1, on_date=today))
        self.assertTrue(self.org1.is_member(self.user1, on_date=yesterday))
        self.assertTrue(m.is_active(on_date=yesterday))
        self.assertFalse(m.is_active(on_date=today))
        self.assertTrue(self.user1 in self.org1.members(on_date=yesterday))
        self.assertFalse(self.user1 in self.org1.members(on_date=today))
        self.assertFalse(self.user1 in self.org1.members())


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
