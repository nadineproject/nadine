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
    print("  package: %s" % bill.membership.package)
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

class UserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        logging.getLogger('nadine.models').setLevel(logging.DEBUG)

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        # self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        # self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        # self.org3 = Organization.objects.create(lead=self.user3, name="User3 Org", created_by=self.user3)
        # self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        # self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        # self.user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')
        # self.user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')

        # Test membership
        self.sub1 = ResourceSubscription.objects.create(
            membership = self.user1.membership,
            resource = Resource.objects.day_resource,
            start_date = two_months_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )

        # Generate all the bills for user1
        self.user1.membership.generate_all_bills()

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

    def test_user_three(self):
        # User 3 = PT15 2/1/2008 - 6/20/2010 & Basic since 6/21/2010
        # Daily activity 6/2/2010 through 6/19/2010
        user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        user3.membership.bill_day = 20
        user3.membership.save()

        user3.membership.set_to_package(self.pt15Package, start_date=date(2008, 2, 1), end_date=date(2010, 6, 20))
        user3.membership.set_to_package(self.basicPackage, start_date=date(2010, 6, 21), end_date=None)
        for day in range(2, 19):
            CoworkingDay.objects.create(user=user3, visit_date=date(2010, 6, day), payment='Bill')

        # print("Bill Count: %d" % UserBill.objects.filter(user=user3).count())
        # user3.membership.generate_all_bills(start_date=date(2010, 6, 20), end_date=date(2010, 7, 20))
        # print("Bill Count: %d" % UserBill.objects.filter(user=user3).count())

        user3.membership.generate_bill(target_date=date(2010, 6, 20))
        bill = user3.bills.get(period_start=date(2010, 6, 20))
        print_bill(bill)
        # Bill total should ber $90: $50 for new basic and $40 for PT-15 overage
        self.assertEqual(90, bill.amount)
        self.assertEqual(17, bill.resource_activity_count(Resource.objects.day_resource))

        # if day.day == 21:
        #     self.assertTrue(member3.last_bill() != None)
        #     self.assertTrue(member3.last_bill().bill_date.month == day.month and member3.last_bill().bill_date.day == day.day)
        #     self.assertEqual(member3.last_bill().dropins.count(), 0)

    def test_user_four(self):
        # User 4 = PT5 2/1/2008 - 6/10/2010 & Resident since 6/11/2010
        # Daily activity 6/2/2010 through 6/11/2010
        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        Membership.objects.create_with_plan(user=self.user4, start_date=date(2008, 2, 1), end_date=date(2010, 6, 10), membership_plan=self.pt5Plan)
        Membership.objects.create_with_plan(user=self.user4, start_date=date(2010, 6, 11), end_date=None, membership_plan=self.residentPlan)
        for day in range(2, 11):
            CoworkingDay.objects.create(user=self.user4, visit_date=date(2010, 6, day), payment='Bill')
        # if day.day == 10:
        #     # User4's PT5 membership
        #     self.assertTrue(member4.last_bill() != None, "Member4 should have had a bill")
        #     self.assertEqual(member4.last_bill().membership.membership_plan, self.pt5Plan)
        #     self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
        #     self.assertEqual(member4.last_bill().membership, Membership.objects.get(user=self.user4, membership_plan=self.pt5Plan.id))
        #     self.assertEqual(member4.last_bill().dropins.count(), 9)  # dropins on 6/2 - 6/10
        #     self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - self.pt5Plan.dropin_allowance) * self.pt5Plan.daily_rate)
        # if day.day == 11:
        #     # User4's Resident membership
        #     self.assertTrue(member4.last_bill() != None)
        #     self.assertEqual(member4.last_bill().membership.membership_plan, self.residentPlan)
        #     self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
        #     self.assertEqual(member4.last_bill().dropins.count(), 0)

    def test_user_five(self):
        # User 5 = PT15 5/20/2010 - 6/16/2010 & Basic since 6/17/2010
        # Daily activity 6/1/2010 through 6/15/2010
        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        Membership.objects.create_with_plan(user=self.user5, start_date=date(2010, 5, 20), end_date=date(2010, 6, 16), membership_plan=self.pt15Plan)
        Membership.objects.create_with_plan(user=self.user5, start_date=date(2010, 6, 17), end_date=None, membership_plan=self.basicPlan)
        for day in range(1, 16):
            CoworkingDay.objects.create(user=self.user5, visit_date=date(2010, 6, day), payment='Bill')
        # if day.day == 16:
        #     # User 5's PT15
        #     # Should be 15 dropins but they were part of the PT15 plan so no extra charges should be on this bill
        #     self.assertTrue(member5.last_bill() != None)
        #     self.assertEqual(member5.last_bill().membership.membership_plan, self.pt15Plan)
        #     self.assertTrue(member5.last_bill().bill_date.month == day.month and member5.last_bill().bill_date.day == day.day)
        #     self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.pt15Plan.id))
        #     #TODOself.assertEqual(member5.last_bill().dropins.count(), 15)
        #     self.assertEqual(member5.last_bill().amount, 0)
        # if day.day == 17:
        #     # User 5's Basic membership
        #     self.assertTrue(member5.last_bill() != None)
        #     self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.basicPlan.id))
        #     self.assertEqual(member5.last_bill().dropins.count(), 0)
        #     self.assertEqual(member5.last_bill().amount, self.basicPlan.monthly_rate)

    def test_user_six(self):
        # User 6, 7 = PT-5 6/26/2008 - User 7 guest of User 6
        # User 7 has daily activity 6/1/2010 through 6/15/2010
        self.user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')
        self.user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
        Membership.objects.create_with_plan(user=self.user6, start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan)
        Membership.objects.create_with_plan(user=self.user7, start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan, rate=0, paid_by=self.user6)
        for day in range(1, 16):
            CoworkingDay.objects.create(user=self.user7, visit_date=date(2010, 6, day), payment='Bill')
        # if day.day == 26:
        #     # User 6's PT-5, User 7's PT-5
        #     # User 7 guest of user 6 and used 15 days
        #     self.assertEqual(member7.is_guest(), self.user6)
        #     self.assertTrue(member7.last_bill() != None)
        #     self.assertEqual(member7.last_bill().dropins.count(), 0)
        #     self.assertEqual(member7.last_bill().amount, 0)
        #     self.assertTrue(member6.last_bill() != None)
        #     self.assertEqual(member6.last_bill().dropins.count(), 0)
        #     self.assertEqual(member6.last_bill().guest_dropins.count(), 15)
        #     # $75 base rate + 10 overage days @ $20 = $275
        #     self.assertEqual(member6.last_bill().amount, 275)

    def test_guest_activity(self):
        test_date = date(2010, 6, 20)
        self.assertEqual(self.user7.profile.is_guest(), self.user6)
        self.assertTrue(self.user7 in self.user6.profile.guests())
        self.assertEqual(len(self.user6.profile.activity_this_month(test_date)), 15)

    # TODO - Remove once ported over
    # def test_run(self):
    #     member3 = self.user3.profile
    #     member4 = self.user4.profile
    #     member5 = self.user5.profile
    #     member6 = self.user6.profile
    #     member7 = self.user7.profile
    #
    #     end_time = datetime(2010, 6, 30)
    #     day_range = range(30)
    #     day_range.reverse()
    #     days = [end_time - timedelta(days=i) for i in day_range]
    #     # 2010-06-1 through 2010-06-30
    #     for day in days:
    #         billing.run_billing(day)
    #         if day.day == 10:
    #             # User4's PT5 membership
    #             self.assertTrue(member4.last_bill() != None, "Member4 should have had a bill")
    #             self.assertEqual(member4.last_bill().membership.membership_plan, self.pt5Plan)
    #             self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
    #             self.assertEqual(member4.last_bill().membership, Membership.objects.get(user=self.user4, membership_plan=self.pt5Plan.id))
    #             self.assertEqual(member4.last_bill().dropins.count(), 9)  # dropins on 6/2 - 6/10
    #             self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - self.pt5Plan.dropin_allowance) * self.pt5Plan.daily_rate)
    #         if day.day == 11:
    #             # User4's Resident membership
    #             self.assertTrue(member4.last_bill() != None)
    #             self.assertEqual(member4.last_bill().membership.membership_plan, self.residentPlan)
    #             self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
    #             self.assertEqual(member4.last_bill().dropins.count(), 0)
    #         if day.day == 16:
    #             # User 5's PT15
    #             # Should be 15 dropins but they were part of the PT15 plan so no extra charges should be on this bill
    #             self.assertTrue(member5.last_bill() != None)
    #             self.assertEqual(member5.last_bill().membership.membership_plan, self.pt15Plan)
    #             self.assertTrue(member5.last_bill().bill_date.month == day.month and member5.last_bill().bill_date.day == day.day)
    #             self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.pt15Plan.id))
    #             #TODOself.assertEqual(member5.last_bill().dropins.count(), 15)
    #             self.assertEqual(member5.last_bill().amount, 0)
    #         if day.day == 17:
    #             # User 5's Basic membership
    #             self.assertTrue(member5.last_bill() != None)
    #             self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.basicPlan.id))
    #             self.assertEqual(member5.last_bill().dropins.count(), 0)
    #             self.assertEqual(member5.last_bill().amount, self.basicPlan.monthly_rate)
    #         if day.day == 20:
    #             # User 3's PT-15 membership
    #             self.assertTrue(member3.last_bill() != None)
    #             self.assertTrue(member3.last_bill().bill_date.month == day.month and member3.last_bill().bill_date.day == day.day)
    #             self.assertEqual(member3.last_bill().dropins.count(), 17)
    #         if day.day == 21:
    #             self.assertTrue(member3.last_bill() != None)
    #             self.assertTrue(member3.last_bill().bill_date.month == day.month and member3.last_bill().bill_date.day == day.day)
    #             self.assertEqual(member3.last_bill().dropins.count(), 0)
    #         if day.day == 26:
    #             # User 6's PT-5, User 7's PT-5
    #             # User 7 guest of user 6 and used 15 days
    #             self.assertEqual(member7.is_guest(), self.user6)
    #             self.assertTrue(member7.last_bill() != None)
    #             self.assertEqual(member7.last_bill().dropins.count(), 0)
    #             self.assertEqual(member7.last_bill().amount, 0)
    #             self.assertTrue(member6.last_bill() != None)
    #             self.assertEqual(member6.last_bill().dropins.count(), 0)
    #             self.assertEqual(member6.last_bill().guest_dropins.count(), 15)
    #             # $75 base rate + 10 overage days @ $20 = $275
    #             self.assertEqual(member6.last_bill().amount, 275)

    def test_last_membership_and_anniversary_day(self):
        # User 1 = Resident since 6/26/2008
        user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        start_date = date(2008, 6, 26)
        Membership.objects.create_with_plan(user=user1, start_date=start_date, end_date=None, membership_plan=self.residentPlan)

        run_billing_for_range(datetime(2010, 6, 30), 30)
        # print_user_data(user1)

        # Has bills
        user_bills = user1.bill_set.all().order_by('-bill_date')
        self.assertTrue(len(user_bills) > 0)

        # Last membership lines up
        last_membership = user1.profile.last_membership()
        self.assertEqual(last_membership, user_bills[0].membership)

        # The bill adds up
        self.assertEqual(user_bills[0].amount, self.residentPlan.monthly_rate)

        # Anniversery membership lines up two years later
        self.assertTrue(last_membership.is_anniversary_day(date(2010, 6, 26)), "6/26/2010 should be an anniversery date of this membership")


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
