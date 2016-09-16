import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import staff.billing as billing
from interlink.models import MailingList
from staff.views.stats import beginning_of_next_month, first_days_in_months
from nadine.models import *


def print_user_data(user):
    print
    profile = user.get_profile()
    print("Profile: %s" % profile)
    for bill in Bill.objects.filter(user=user):
        print("  Bill: %s" % bill)
        print("    Membership: %s" % bill.membership)
        for dropin in bill.dropins.all():
            print("    Drop-in: %s" % dropin)


def run_billing_for_range(end_time, days):
    day_range = range(days)
    day_range.reverse()
    for i in day_range:
        day = end_time - timedelta(days=i)
        billing.run_billing(day)


class BillingTestCase(TestCase):

    def setUp(self):
        self.basicPlan = MembershipPlan.objects.create(name="Basic", monthly_rate=50, dropin_allowance=3, daily_rate=20, has_desk=False)
        self.pt5Plan = MembershipPlan.objects.create(name="PT5", monthly_rate=75, dropin_allowance=5, daily_rate=20, has_desk=False)
        self.pt15Plan = MembershipPlan.objects.create(name="PT15", monthly_rate=225, dropin_allowance=15, daily_rate=20, has_desk=False)
        self.residentPlan = MembershipPlan.objects.create(name="Resident", monthly_rate=475, dropin_allowance=5, daily_rate=20, has_desk=True)

        # User 3 = PT15 2/1/2008 - 6/20/2010 & Basic since 6/21/2010
        # Daily activity 6/2/2010 through 6/19/2010
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        Membership.objects.create_with_plan(user=self.user3, start_date=date(2008, 2, 1), end_date=date(2010, 6, 20), membership_plan=self.pt15Plan)
        Membership.objects.create_with_plan(user=self.user3, start_date=date(2010, 6, 21), end_date=None, membership_plan=self.basicPlan)
        for day in range(2, 19):
            CoworkingDay.objects.create(user=self.user3, visit_date=date(2010, 6, day), payment='Bill')

        # User 4 = PT5 2/1/2008 - 6/10/2010 & Resident since 6/11/2010
        # Daily activity 6/2/2010 through 6/11/2010
        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        Membership.objects.create_with_plan(user=self.user4, start_date=date(2008, 2, 1), end_date=date(2010, 6, 10), membership_plan=self.pt5Plan)
        Membership.objects.create_with_plan(user=self.user4, start_date=date(2010, 6, 11), end_date=None, membership_plan=self.residentPlan)
        for day in range(2, 11):
            CoworkingDay.objects.create(user=self.user4, visit_date=date(2010, 6, day), payment='Bill')

        # User 5 = PT15 5/20/2010 - 6/16/2010 & Basic since 6/17/2010
        # Daily activity 6/1/2010 through 6/15/2010
        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        Membership.objects.create_with_plan(user=self.user5, start_date=date(2010, 5, 20), end_date=date(2010, 6, 16), membership_plan=self.pt15Plan)
        Membership.objects.create_with_plan(user=self.user5, start_date=date(2010, 6, 17), end_date=None, membership_plan=self.basicPlan)
        for day in range(1, 16):
            CoworkingDay.objects.create(user=self.user5, visit_date=date(2010, 6, day), payment='Bill')

        # User 6, 7 = PT-5 6/26/2008 - User 7 guest of User 6
        # User 7 has daily activity 6/1/2010 through 6/15/2010
        self.user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')
        self.user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
        Membership.objects.create_with_plan(user=self.user6, start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan)
        Membership.objects.create_with_plan(user=self.user7, start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan, rate=0, paid_by=self.user6)
        for day in range(1, 16):
            CoworkingDay.objects.create(user=self.user7, visit_date=date(2010, 6, day), payment='Bill')

    def test_guest_activity(self):
        test_date = date(2010, 6, 20)
        member6 = self.user6.get_profile()
        member7 = self.user7.get_profile()
        self.assertEqual(member7.is_guest(), member6.user)
        self.assertTrue(self.user7 in member6.guests())
        self.assertEqual(len(member6.activity_this_month(test_date)), 15)

    def test_run(self):
        member3 = self.user3.get_profile()
        member4 = self.user4.get_profile()
        member5 = self.user5.get_profile()
        member6 = self.user6.get_profile()
        member7 = self.user7.get_profile()

        end_time = datetime(2010, 6, 30)
        day_range = range(30)
        day_range.reverse()
        days = [end_time - timedelta(days=i) for i in day_range]
        # 2010-06-1 through 2010-06-30
        for day in days:
            billing.run_billing(day)
            if day.day == 10:
                # User4's PT5 membership
                self.assertTrue(member4.last_bill() != None, "Member4 should have had a bill")
                self.assertEqual(member4.last_bill().membership.membership_plan, self.pt5Plan)
                self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
                self.assertEqual(member4.last_bill().membership, Membership.objects.get(user=self.user4, membership_plan=self.pt5Plan.id))
                self.assertEqual(member4.last_bill().dropins.count(), 9)  # dropins on 6/2 - 6/10
                self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - self.pt5Plan.dropin_allowance) * self.pt5Plan.daily_rate)
            if day.day == 11:
                # User4's Resident membership
                self.assertTrue(member4.last_bill() != None)
                self.assertEqual(member4.last_bill().membership.membership_plan, self.residentPlan)
                self.assertTrue(member4.last_bill().bill_date.month == day.month and member4.last_bill().bill_date.day == day.day)
                self.assertEqual(member4.last_bill().dropins.count(), 0)
            if day.day == 16:
                # User 5's PT15
                # Should be 15 dropins but they were part of the PT15 plan so no extra charges should be on this bill
                self.assertTrue(member5.last_bill() != None)
                self.assertEqual(member5.last_bill().membership.membership_plan, self.pt15Plan)
                self.assertTrue(member5.last_bill().bill_date.month == day.month and member5.last_bill().bill_date.day == day.day)
                self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.pt15Plan.id))
                #TODOself.assertEqual(member5.last_bill().dropins.count(), 15)
                self.assertEquals(member5.last_bill().amount, 0)
            if day.day == 17:
                # User 5's Basic membership
                self.assertTrue(member5.last_bill() != None)
                self.assertEqual(member5.last_bill().membership, Membership.objects.get(user=self.user5, membership_plan=self.basicPlan.id))
                self.assertEqual(member5.last_bill().dropins.count(), 0)
                self.assertEquals(member5.last_bill().amount, self.basicPlan.monthly_rate)
            if day.day == 20:
                # User 3's PT-15 membership
                self.assertTrue(member3.last_bill() != None)
                self.assertTrue(member3.last_bill().bill_date.month == day.month and member3.last_bill().bill_date.day == day.day)
                self.assertEqual(member3.last_bill().dropins.count(), 17)
            if day.day == 21:
                self.assertTrue(member3.last_bill() != None)
                self.assertTrue(member3.last_bill().bill_date.month == day.month and member3.last_bill().bill_date.day == day.day)
                self.assertEqual(member3.last_bill().dropins.count(), 0)
            if day.day == 26:
                # User 6's PT-5, User 7's PT-5
                # User 7 guest of user 6 and used 15 days
                self.assertEqual(member7.is_guest(), self.user6)
                self.assertTrue(member7.last_bill() != None)
                self.assertEqual(member7.last_bill().dropins.count(), 0)
                self.assertEquals(member7.last_bill().amount, 0)
                self.assertTrue(member6.last_bill() != None)
                self.assertEqual(member6.last_bill().dropins.count(), 0)
                self.assertEqual(member6.last_bill().guest_dropins.count(), 15)
                # $75 base rate + 10 overage days @ $20 = $275
                self.assertEquals(member6.last_bill().amount, 275)

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
        last_membership = user1.get_profile().last_membership()
        self.assertEqual(last_membership, user_bills[0].membership)

        # The bill adds up
        self.assertEqual(user_bills[0].amount, self.residentPlan.monthly_rate)

        # Anniversery membership lines up two years later
        self.assertTrue(last_membership.is_anniversary_day(date(2010, 6, 26)), "6/26/2010 should be an anniversery date of this membership")

    def test_drop_in_on_billing_date_is_associated_with_correct_bill(self):
        # User 8 = PT-5 5/20/2010 - 6/19/2010 & Basic since 6/20/2010
        # Daily activity 6/11/2010 through 6/23/2010
        user8 = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')
        Membership.objects.create_with_plan(user=user8, start_date=date(2010, 5, 20), end_date=date(2010, 6, 19), membership_plan=self.pt5Plan)
        Membership.objects.create_with_plan(user=user8, start_date=date(2010, 6, 20), end_date=None, membership_plan=self.basicPlan)
        for day in range(11, 23):
            CoworkingDay.objects.create(user=user8, visit_date=date(2010, 6, day), payment='Bill')
        run_billing_for_range(datetime(2010, 7, 31), 61)
        print_user_data(user8)

        bills = Bill.objects.filter(user=user8).order_by("bill_date")
        # self.assertEqual(bills.count(), 5, "Member8 had the incorrect number of bills (%d)" % bills.count())
        may_20_pt5 = bills[0]
        may_20_overage = bills[1]
        june_20_basic = bills[2]
        june_20_overage = bills[3]
        #july_20_basic = bills[4]

        # First bill is just a PT-5
        self.assertTrue(may_20_pt5 != None)
        self.assertEqual(may_20_pt5.membership.membership_plan, self.pt5Plan)
        self.assertEqual(date(2010, 5, 20), may_20_pt5.bill_date)
        self.assertEqual(0, may_20_pt5.dropins.count())

        # Second bill is for 4 overage days on the last day of their membership
        self.assertTrue(may_20_overage != None)
        self.assertEqual(may_20_overage.membership.membership_plan, self.pt5Plan)
        self.assertEqual(date(2010, 6, 19), may_20_overage.bill_date)
        self.assertEqual(9, may_20_overage.dropins.count())
        self.assertEqual(4, may_20_overage.overage_days())
        self.assertEqual(80, may_20_overage.amount)

        # Third bill is for the new Basic membership
        self.assertTrue(june_20_basic != None)
        self.assertEqual(june_20_basic.membership.membership_plan, self.basicPlan)
        self.assertEqual(date(2010, 6, 20), june_20_basic.bill_date)
        self.assertEqual(0, june_20_basic.dropins.count())

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
