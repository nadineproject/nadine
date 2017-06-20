import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import UserBill, Payment
from nadine.models.membership import Membership, ResourceSubscription, MembershipPackage, SubscriptionDefault
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
    print("  package name: %s" % bill.membership.package_name())
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

class MembershipAndUserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        logging.getLogger('nadine.models').setLevel(logging.DEBUG)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')

        # Test membership
        self.sub1 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )

        # Generate all the bills for user1
        # self.user1.membership.generate_all_bills()

        # Packages
        self.pt5Package = MembershipPackage.objects.create(name="PT5")
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 100,
            allowance = 5,
            overage_rate = 20,
        )
        self.pt15Package = MembershipPackage.objects.create(name="PT15")
        SubscriptionDefault.objects.create(
            package = self.pt15Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 225,
            allowance = 15,
            overage_rate = 20,
        )
        self.residentPackage = MembershipPackage.objects.create(name="Resident")
        SubscriptionDefault.objects.create(
            package = self.residentPackage,
            resource = Resource.objects.desk_resource,
            monthly_rate = 395,
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
        self.t40Package = MembershipPackage.objects.create(name="T40")
        SubscriptionDefault.objects.create(
            package = self.t40Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 720,
            allowance = 40,
            overage_rate = 20
        )
        self.teamPackage = MembershipPackage.objects.create(name="Team")
        SubscriptionDefault.objects.create(
            package = self.teamPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 0,
            allowance = 0,
            overage_rate = 0
        )


    def test_start_package(self):
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        user.membership.bill_day = 1
        user.membership.set_to_package(self.pt5Package, start_date=date(2017, 6, 1))
        self.assertEqual(1, user.membership.bill_day)
        self.assertEqual(5, user.membership.allowance_by_resource(resource=1))
        self.assertEqual('PT5', user.membership.package_name())

        user.membership.generate_bills(target_date=date(2017, 7, 1))
        july_bill = user.bills.get(period_start=date(2017, 7, 1))
        self.assertTrue(july_bill != None)
        self.assertEqual(100, july_bill.amount)
        

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
