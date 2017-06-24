import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from django.urls import reverse
from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import UserBill, BillLineItem, Payment
from nadine.models.membership import MembershipPackage, SubscriptionDefault
from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.organization import Organization
from nadine.models.resource import Resource
from nadine.models.usage import CoworkingDay

today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)

def print_all_bills(user):
    for bill in UserBill.objects.filter(user=user):
        print_bill(bill)

def print_bill(bill):
    print("UserBill %d" % bill.id)
    print("  due_date: %s" % bill.due_date)
    print("  package name: %s" % bill.membership.package_name())
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

class UserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        # logging.getLogger('nadine.models').setLevel(logging.DEBUG)
        logging.getLogger('nadine.models').setLevel(logging.INFO)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')

    def test_unpaid(self):
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertEqual(0, bill.amount)
        self.assertEqual(0, bill.total_owed)
        self.assertFalse(bill in UserBill.objects.unpaid())
        # Create a line item
        BillLineItem.objects.create(bill=bill, amount=10)
        self.assertEqual(10, bill.amount)
        self.assertEqual(10, bill.total_owed)
        self.assertTrue(bill in UserBill.objects.unpaid())
        # Pay the bill
        Payment.objects.create(bill=bill, user=self.user1, amount=10)
        self.assertEqual(0, bill.total_owed)
        self.assertFalse(bill in UserBill.objects.unpaid())

    def test_unpaid_partial_payment(self):
        # Apply $1 to the last bill and make sure it's still in our unpaid set
        bill = UserBill.objects.create_for_day(self.user1, today)
        BillLineItem.objects.create(bill=bill, amount=10)
        self.assertEqual(10, bill.amount)
        Payment.objects.create(bill=bill, user=self.user1, amount=1)
        self.assertTrue(bill.total_paid == 1)
        self.assertFalse(bill.is_paid)
        self.assertTrue(bill in UserBill.objects.unpaid())

    def test_open_and_closed(self):
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertTrue(bill in UserBill.objects.open())
        self.assertFalse(bill in UserBill.objects.closed())
        bill.close()
        self.assertFalse(bill in UserBill.objects.open())
        self.assertTrue(bill in UserBill.objects.closed())

    def test_add_subscription(self):
        subscription = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            monthly_rate = Decimal(100.00),
            overage_rate = 0,
        )
        bill = UserBill.objects.create_for_day(self.user1)
        self.assertFalse(bill.has_subscription(subscription))
        bill.add_subscription(subscription)
        self.assertTrue(bill.has_subscription(subscription))

    def test_add_coworking_day(self):
        day = CoworkingDay.objects.create(
            user = self.user1,
            visit_date = today
        )
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertFalse(bill.has_coworking_day(day))
        bill.add_coworking_day(day)
        self.assertTrue(bill.has_coworking_day(day))
        self.assertEquals(bill, day.bill)

    def test_resource_allowance(self):
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertEqual(0, bill.resource_allowance(Resource.objects.day_resource))
        subscription1 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            allowance = 10,
            monthly_rate = Decimal(100.00),
            overage_rate = 0,
        )
        bill.add_subscription(subscription1)
        self.assertEqual(10, bill.resource_allowance(Resource.objects.day_resource))
        # Try to fake it out by adding the subscription again
        bill.add_subscription(subscription1)
        self.assertEqual(10, bill.resource_allowance(Resource.objects.day_resource))
        subscription2 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            allowance = 8,
            monthly_rate = Decimal(100.00),
            overage_rate = 0,
        )
        bill.add_subscription(subscription2)
        self.assertEqual(18, bill.resource_allowance(Resource.objects.day_resource))


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
