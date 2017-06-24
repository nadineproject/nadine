import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import BillingBatch, UserBill, Payment
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
    print("  user: %s" % bill.user)
    print("  due_date: %s" % bill.due_date)
    print("  period_start: %s" % bill.period_start)
    print("  period_end: %s" % bill.period_end)
    if bill.is_closed:
        print("  closed_ts: %s" % bill.closed_ts)
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

class BillingTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        # logging.getLogger('nadine.models').setLevel(logging.DEBUG)
        logging.getLogger('nadine.models').setLevel(logging.INFO)

        # Basic Package
        self.basicPackage = MembershipPackage.objects.create(name="Basic")
        SubscriptionDefault.objects.create(
            package = self.basicPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 50,
            allowance = 3,
            overage_rate = 15,
        )

        # PT5 Package
        self.pt5Package = MembershipPackage.objects.create(name="PT5")
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 75,
            allowance = 5,
            overage_rate = 20,
        )

        # PT15 Packge
        self.pt15Package = MembershipPackage.objects.create(name="PT15")
        SubscriptionDefault.objects.create(
            package = self.pt15Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 225,
            allowance = 15,
            overage_rate = 20,
        )

        # Resident Package
        self.residentPackage = MembershipPackage.objects.create(name="Resident")
        SubscriptionDefault.objects.create(
            package = self.residentPackage,
            resource = Resource.objects.desk_resource,
            monthly_rate = 475,
            allowance = 1,
            overage_rate = 0,
        )
        SubscriptionDefault.objects.create(
            package = self.residentPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 0,
            allowance = 5,
            overage_rate = 20,
        )

    def test_drop_in_on_billing_date_is_associated_with_correct_bill(self):
        # PT-5 5/20/2010 - 6/19/2010 & Basic since 6/20/2010
        # Daily activity 6/11/2010 through 6/25/2010
        user = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')
        user.membership.bill_day = 20
        user.membership.save()
        user.membership.set_to_package(self.pt5Package, start_date=date(2010, 5, 20), end_date=date(2010, 6, 19))
        user.membership.set_to_package(self.basicPackage, start_date=date(2010, 6, 20))
        days = {}
        for day in range(11, 25):
            visit_date = date(2010, 6, day)
            days[visit_date] = CoworkingDay.objects.create(user=user, visit_date=visit_date, payment='Bill')

        # Run the billing batch
        batch = BillingBatch.objects.run(start_date=date(2010, 5, 20), end_date=date(2010, 7, 20))
        self.assertTrue(batch.successful)
        self.assertEqual(3, batch.bills.count())
        # print_all_bills(user)

        # May 20th bill = PT5 with 9 days
        # Total = $75 + 4 * $20 = $155
        self.assertEqual(user.membership.matching_package(date(2010, 5, 20)), self.pt5Package)
        may_20_bill = user.bills.get(period_start=date(2010, 5, 20))
        self.assertTrue(may_20_bill != None)
        self.assertEqual(155.00, may_20_bill.amount)
        self.assertEqual(9, may_20_bill.coworking_days().count())
        self.assertTrue(days[date(2010, 6, 11)] in may_20_bill.coworking_days())
        self.assertTrue(days[date(2010, 6, 19)] in may_20_bill.coworking_days())
        self.assertFalse(days[date(2010, 6, 20)] in may_20_bill.coworking_days())
        self.assertTrue(may_20_bill.is_closed)

        # June 20th bill = Basic + 2 overage
        # Total = $50 + 2 * $15 = $80
        june_20_bill = user.bills.get(period_start=date(2010, 6, 20))
        self.assertTrue(june_20_bill != None)
        self.assertEqual(80, june_20_bill.amount)
        self.assertEqual(5, june_20_bill.coworking_days().count())
        self.assertFalse(days[date(2010, 6, 19)] in june_20_bill.coworking_days())
        self.assertTrue(days[date(2010, 6, 20)] in june_20_bill.coworking_days())
        self.assertTrue(days[date(2010, 6, 24)] in june_20_bill.coworking_days())
        self.assertTrue(june_20_bill.is_closed)

    def test_guest_membership_bills(self):
        # User 6 & 7 = PT-5 starting 1/1/2008
        # User 7 guest of User 6
        user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')
        user6.membership.set_to_package(self.pt5Package, start_date=date(2008, 1, 1), end_date=None, bill_day=1)
        user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
        user7.membership.set_to_package(self.pt5Package, start_date=date(2008, 1, 1), paid_by=user6, bill_day=1)
        user8 = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')

        # User 7 has daily activity 6/1/2010 through 6/15/2010
        days = {}
        for day in range(1, 16):
            visit_date = date(2010, 6, day)
            days[visit_date] = CoworkingDay.objects.create(user=user7, visit_date=visit_date, payment='Bill')
        # User 8 has 1 visit on 6/10/2010 guest of User 6
        user8_visit = CoworkingDay.objects.create(user=user8, paid_by=user6, visit_date=date(2010, 6, 1), payment='Bill')

        # Run the billing batch for June only
        batch = BillingBatch.objects.run(start_date=date(2010, 6, 1), end_date=date(2010, 6, 30))
        self.assertTrue(batch.successful)
        # self.assertEqual(3, batch.bills.count())
        print_all_bills(user6)
        print_all_bills(user7)

        # User 7 is a guest of User 6
        self.assertTrue(user7.profile.is_guest())
        self.assertTrue(user6 in user7.profile.hosts())
        self.assertTrue(user7 in user6.profile.guests())

        # Total: $75 * 2 + 6 Overage Days at $20 = $270
        bill = user6.bills.get(period_start=date(2010, 6, 1))
        self.assertEqual(270, bill.amount)
        self.assertEqual(10, bill.resource_allowance(Resource.objects.day_resource))
        self.assertEqual(16, bill.coworking_days().count())
        self.assertTrue(user8_visit in bill.coworking_days())

        # User 6 owes $270, User 7 and User 8 owe $0
        self.assertEqual(270, user6.profile.open_bills_amount)
        self.assertEqual(0, user7.profile.open_bills_amount)
        self.assertEqual(0, user8.profile.open_bills_amount)

    def test_change_bill_day(self):
        # PT5 from 1/10/2010 billed on the 10th
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        user.membership.bill_day = 10
        user.membership.set_to_package(self.pt5Package, start_date=date(2010, 1, 10))
        self.assertEqual(10, user.membership.bill_day)

        # Two days of activity on 6/9 and 6/15
        # First day is in the 6/10 bill, second is not
        day1 = CoworkingDay.objects.create(user=user, visit_date=date(2010, 6, 9), payment='Bill')
        day2 = CoworkingDay.objects.create(user=user, visit_date=date(2010, 6, 15), payment='Bill')

        batch = BillingBatch.objects.run(start_date=date(2010, 6, 10), end_date=date(2010, 6, 10))
        self.assertTrue(batch.successful)
        june_10_bill = user.bills.get(period_start=date(2010, 6, 10))
        self.assertTrue(day1 in june_10_bill.coworking_days())
        self.assertEqual(june_10_bill, day1.bill)
        self.assertFalse(day2 in june_10_bill.coworking_days())

        # Before we change our bill day we need to remove outstanding bills
        june_10_bill.delete()

        # Change the bill date to the 1st
        user.membership.bill_day = 1
        user.membership.save()
        self.assertEqual(1, user.membership.bill_day)

        # Generate the July 1st bill
        batch = BillingBatch.objects.run(start_date=date(2010, 6, 1), end_date=date(2010, 7, 1))
        self.assertTrue(batch.successful)

        june_1_bill = user.bills.get(period_start=date(2010, 6, 1))
        self.assertTrue(day1 in june_1_bill.coworking_days())
        self.assertTrue(day2 in june_1_bill.coworking_days())

        july_1_bill = user.bills.get(period_start=date(2010, 7, 1))
        self.assertFalse(day1 in july_1_bill.coworking_days())
        self.assertFalse(day2 in july_1_bill.coworking_days())

    # def test_prorated_subscription(self):
    #     # User 1 is a PT5 from 1/1/2010 1st
    #     user = User.objects.create(username='test_user', first_name='Test', last_name='User')
    #     user.membership.bill_day = 1
    #     user.membership.set_to_package(self.pt5Package, start_date=date(2010, 1, 10))


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
