import traceback
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import UserBill, Payment
from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.resource import Resource
from nadine.models.organization import Organization

today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)

class UserBillTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.org3 = Organization.objects.create(lead=self.user3, name="User3 Org", created_by=self.user3)

        # Resources
        self.test_resource = Resource.objects.create(name="Test Resource")

        # Test membership
        self.sub1 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = self.test_resource,
            start_date = two_months_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )

        # Generate all the bills for user1
        self.user1.membership.generate_all_bills()

    def test_unpaid(self):
        # 1 = Month before last
        # 2 = Last month
        # 3 = Today
        self.assertEqual(3, UserBill.objects.unpaid().count())

    def test_unpaid_in_progress(self):
        # Mark the last bill in progress and check the counts
        last_bill = UserBill.objects.unpaid().last()
        last_bill.in_progress = True
        last_bill.save()
        self.assertEqual(1, UserBill.objects.unpaid(in_progress=True).count())
        self.assertTrue(last_bill in UserBill.objects.unpaid(in_progress=True))
        self.assertEqual(2, UserBill.objects.unpaid(in_progress=False).count())
        self.assertFalse(last_bill in UserBill.objects.unpaid(in_progress=False))

    def test_unpaid_partial_payment(self):
        # Apply $1 to the last bill and make sure it's still in our unpaid set
        last_bill = UserBill.objects.unpaid().last()
        Payment.objects.create(bill=last_bill, user=self.user1, paid_amount=1)
        self.assertTrue(last_bill.total_paid == 1)
        self.assertFalse(last_bill.is_paid)
        self.assertTrue(last_bill in UserBill.objects.unpaid())


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
