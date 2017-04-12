import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import UserBill, Payment
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

def print_bill(bill):
    print("UserBill %d" % bill.id)
    print("  due_date: %s" % bill.due_date)
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

class UserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        logging.getLogger('nadine.models').setLevel(logging.DEBUG)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.org3 = Organization.objects.create(lead=self.user3, name="User3 Org", created_by=self.user3)

        # Test membership
        self.sub1 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )

        # Packages
        self.basicPackage = MembershipPackage.objects.create(name="Basic")
        SubscriptionDefault.objects.create(
            package = self.basicPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 50,
            allowance = 3,
            overage_rate = 15,
        )
        self.pt5Package = MembershipPackage.objects.create(name="PT5")
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 75,
            allowance = 5,
            overage_rate = 20,
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

    def test_drop_in_on_billing_date_is_associated_with_correct_bill(self):
        # User 8 = PT-5 5/20/2010 - 6/19/2010 & Basic since 6/20/2010
        # Daily activity 6/11/2010 through 6/25/2010
        user8 = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')
        user8.membership.bill_day = 20
        user8.membership.save()
        user8.membership.set_to_package(self.pt5Package, start_date=date(2010, 5, 20), end_date=date(2010, 6, 19))
        user8.membership.set_to_package(self.basicPackage, start_date=date(2010, 6, 20))
        for day in range(11, 25):
            CoworkingDay.objects.create(user=user8, visit_date=date(2010, 6, day), payment='Bill')

        # May 20th bill = PT5 - No overage from previous period
        self.assertEqual(user8.membership.matching_package(date(2010, 5, 20)), self.pt5Package)
        user8.membership.generate_bill(target_date=date(2010, 5, 20))
        may_20_bill = user8.bills.get(period_start=date(2010, 5, 20))
        print_bill(may_20_bill)
        self.assertTrue(may_20_bill != None)
        self.assertEqual(date(2010, 5, 20), may_20_bill.due_date)
        self.assertEqual(75.00, may_20_bill.amount)
        self.assertEqual(0, may_20_bill.resource_activity_count(Resource.objects.day_resource))

        # June 20th bill = Basic + 4 over PT5 from previous period
        self.assertEqual(user8.membership.matching_package(date(2010, 6, 20)), self.basicPackage)
        user8.membership.generate_bill(target_date=date(2010, 6, 20))
        june_20_bill = user8.bills.get(period_start=date(2010, 6, 20))
        print_bill(june_20_bill)
        self.assertTrue(june_20_bill != None)
        self.assertEqual(date(2010, 6, 20), june_20_bill.due_date)
        self.assertEqual(130, june_20_bill.amount)
        self.assertEqual(9, june_20_bill.resource_activity_count(Resource.objects.day_resource))


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
