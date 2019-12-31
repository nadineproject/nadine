import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from django.urls import reverse
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import UserBill, BillLineItem, Payment
from nadine.models.membership import MembershipPackage, SubscriptionDefault
from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.organization import Organization
from nadine.models.resource import Resource, Room
from nadine.models.usage import CoworkingDay, Event


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
    print(("UserBill %d" % bill.id))
    print(("  due_date: %s" % bill.due_date))
    print(("  amount: $%s" % bill.amount))
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print(("    %s: $%s" % (line_item.description, line_item.amount)))


@override_settings(SUSPEND_MEMBER_ALERTS=True)
class UserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        # logging.getLogger('nadine.models').setLevel(logging.DEBUG)
        logging.getLogger('nadine.models').setLevel(logging.INFO)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')

        self.test_room = Room.objects.create(
            name = "Test Room",
            floor = 2,
            seats = 6,
            max_capacity = 10,
            default_rate = 50,
        )

    def test_outstanding(self):
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertEqual(0, bill.amount)
        self.assertEqual(0, bill.total_owed)
        self.assertFalse(bill in UserBill.objects.outstanding())
        # Create a line item
        lineitem = BillLineItem.objects.create(bill=bill, amount=10)
        self.assertEqual(10, bill.amount)
        self.assertEqual(10, bill.total_owed)
        self.assertTrue(bill in UserBill.objects.outstanding())
        # Pay the bill
        payment = Payment.objects.create(bill=bill, user=self.user1, amount=10)
        self.assertEqual(0, bill.total_owed)
        self.assertFalse(bill in UserBill.objects.outstanding())
        # Delete the payment
        payment.delete()
        self.assertEqual(10, bill.amount)
        self.assertEqual(10, bill.total_owed)
        self.assertTrue(bill in UserBill.objects.outstanding())
        # Delete the line item
        lineitem.delete()
        self.assertEqual(0, bill.total_owed)
        self.assertFalse(bill in UserBill.objects.outstanding())

    def test_outstanding_partial_payment(self):
        # Apply $1 to a $10 bill and make sure it's still in our outstanding set
        bill = UserBill.objects.create_for_day(self.user1, today)
        BillLineItem.objects.create(bill=bill, amount=10)
        self.assertEqual(10, bill.amount)
        Payment.objects.create(bill=bill, user=self.user1, amount=1)
        self.assertTrue(bill.total_paid == 1)
        self.assertFalse(bill.is_paid)
        self.assertEqual(9, bill.total_owed)
        self.assertTrue(bill in UserBill.objects.outstanding())

    def test_outstanding_partial_payment_bug300(self):
        # A bug was identified where a bill with many line items doesn't
        # show up as outstanding if there is a partial payment.
        # Django Bug:  https://code.djangoproject.com/ticket/10060
        # Nadine Bug:  https://github.com/nadineproject/nadine/issues/300
        bill = UserBill.objects.create_for_day(self.user1, today)
        for i in range(0, 10):
            BillLineItem.objects.create(bill=bill, amount=1)
        self.assertEqual(10, bill.amount)
        Payment.objects.create(bill=bill, user=self.user1, amount=1)
        self.assertTrue(bill.total_paid == 1)
        self.assertFalse(bill.is_paid)
        self.assertEqual(9, bill.total_owed)
        self.assertTrue(bill in UserBill.objects.outstanding())

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
        self.assertFalse(bill.includes_coworking_day(day))
        bill.add_coworking_day(day)
        self.assertTrue(bill.includes_coworking_day(day))
        self.assertEqual(bill, day.bill)

    def test_add_event(self):
        event = Event.objects.create(
            user = self.user1,
            room = self.test_room,
            start_ts = localtime(now()),
            end_ts = localtime(now()) + timedelta(hours=2),
        )
        bill = UserBill.objects.create_for_day(self.user1, today)
        self.assertFalse(bill.includes_event(event))
        bill.add_event(event)
        self.assertTrue(bill.includes_event(event))
        self.assertEqual(bill, event.bill)
        self.assertEqual(2, bill.event_hours_used)
        self.assertTrue(1 == bill.event_count)

    def test_monthly_rate(self):
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
        self.assertEqual(100.00, bill.monthly_rate)
        # Add another subscription
        subscription2 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            allowance = 8,
            monthly_rate = Decimal(87.00),
            overage_rate = 0,
        )
        bill.add_subscription(subscription2)
        self.assertEqual(187.00, bill.monthly_rate)

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

    def test_recalculate(self):
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        membership = Membership.objects.for_user(user)
        bill = UserBill.objects.create(user=user, period_start=one_month_ago, period_end=today, due_date=today)

        # Add a day w/o any subscriptions and expect to be charged
        day1 = CoworkingDay.objects.create(user=user, visit_date=yesterday, payment='Bill')
        bill.add_coworking_day(day1)
        self.assertEqual(bill.amount, Resource.objects.day_resource.default_rate)

        # Add a day subscription and expect the amount to the one day and the monthly_rate
        subscription = ResourceSubscription.objects.create(membership=membership, resource=Resource.objects.day_resource, allowance=3, start_date=one_month_ago, end_date=one_month_from_now, monthly_rate=Decimal(50.00), overage_rate=0)
        bill.add_subscription(subscription)
        self.assertEqual(bill.amount, subscription.monthly_rate + Resource.objects.day_resource.default_rate)

        # Recalculate and expect the amount to be just the monthly_rate
        bill.recalculate()
        self.assertEqual(bill.amount, subscription.monthly_rate)

    def test_combine(self):
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        membership = Membership.objects.for_user(user)

        # Bill1 is for last month and bill2 is for next month
        bill1 = UserBill.objects.create(user=user, period_start=one_month_ago, period_end=today, due_date=today)
        bill2 = UserBill.objects.create(user=user, period_start=tomorrow, period_end=one_month_from_now, due_date=one_month_from_now)

        # Subscription1 is for a day and subscription2 is for a key
        subscription1 = ResourceSubscription.objects.create(membership=membership, resource=Resource.objects.day_resource, start_date=one_month_ago, end_date=one_month_from_now, monthly_rate=Decimal(100.00), overage_rate=0)
        subscription2 = ResourceSubscription.objects.create(membership=membership, resource=Resource.objects.key_resource, start_date=one_month_ago, end_date=one_month_from_now, monthly_rate=Decimal(100.00), overage_rate=0)
        bill1.add_subscription(subscription1)
        bill2.add_subscription(subscription2)
        self.assertTrue(bill1.has_subscription(subscription1))
        self.assertFalse(bill1.has_subscription(subscription2))
        self.assertTrue(bill2.has_subscription(subscription2))
        self.assertFalse(bill2.has_subscription(subscription1))

        # Add a few coworking days
        day1 = CoworkingDay.objects.create(user=user, visit_date=yesterday, payment='Bill')
        day2 = CoworkingDay.objects.create(user=user, visit_date=tomorrow, payment='Bill')
        bill1.add_coworking_day(day1)
        bill2.add_coworking_day(day2)
        self.assertTrue(bill1.includes_coworking_day(day1))
        self.assertFalse(bill1.includes_coworking_day(day2))
        self.assertTrue(bill2.includes_coworking_day(day2))
        self.assertFalse(bill2.includes_coworking_day(day1))

        # Combine the new bills
        bill1.combine(bill2)
        self.assertEqual(None, UserBill.objects.filter(id=bill2.id).first())
        self.assertEqual(bill1.period_start, one_month_ago)
        self.assertEqual(bill1.period_end, one_month_from_now)
        self.assertEqual(bill1.due_date, one_month_from_now)
        self.assertTrue(bill1.has_subscription(subscription1))
        self.assertTrue(bill1.has_subscription(subscription2))
        self.assertTrue(bill1.includes_coworking_day(day1))
        self.assertTrue(bill1.includes_coworking_day(day2))

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
