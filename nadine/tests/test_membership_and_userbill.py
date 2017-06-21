import traceback, logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User
from django.db.models import Sum

from nadine.models.billing import UserBill, Payment
from nadine.models.membership import Membership, ResourceSubscription, MembershipPackage, SubscriptionDefault
from nadine.models.resource import Resource
from nadine.models.usage import CoworkingDay


today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_week_from_now = today + timedelta(days=7)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)
two_weeks_ago = today - timedelta(days=14)
two_weeks_from_now = today + timedelta(days=14)

def print_bill(bill):
    print("UserBill %d" % bill.id)
    print("  due_date: %s" % bill.due_date)
    print("  package name: %s" % bill.membership.package_name())
    print("  amount: $%s" % bill.amount)
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print("    %s: $%s" % (line_item.description, line_item.amount))

def print_all_bills(user):
    for bill in UserBill.objects.filter(user=user):
        print_bill(bill)

class MembershipAndUserBillTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        logging.getLogger('nadine.models').setLevel(logging.DEBUG)

        self.user1 = User.objects.create(username='user_one', first_name='User', last_name='One')

        # Generate all the bills for user1
        # self.user1.membership.generate_all_bills()

        # Packages
        self.advocatePackage = MembershipPackage.objects.create(name='Advocate')
        SubscriptionDefault.objects.create(
            package=self.advocatePackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 30,
            overage_rate = 20,
        )
        self.pt5Package = MembershipPackage.objects.create(name="PT5")
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 100,
            allowance = 5,
            overage_rate = 20,
        )
        self.pt10Package = MembershipPackage.objects.create(name="PT10")
        SubscriptionDefault.objects.create(
            package = self.pt10Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 180,
            allowance = 10,
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
        #New user joins and starts a PT5 membership the same day
        user = User.objects.create(username='member_one', first_name='Member', last_name='One')
        user.membership.bill_day = 1
        user.membership.set_to_package(self.pt5Package, start_date=date(2017, 6, 1))
        self.assertEqual(1, user.membership.bill_day)
        self.assertEqual(5, user.membership.allowance_by_resource(resource=1))
        self.assertEqual('PT5', user.membership.package_name())

        user.membership.generate_bills(target_date=date(2017, 7, 1))
        july_bill = user.bills.get(period_start=date(2017, 7, 1))
        self.assertTrue(july_bill != None)
        self.assertEqual(100, july_bill.amount)

    def test_backdated_new_user_and_membership(self):
        # New user starts Advocate membership backdated 2 weeks
        user = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.assertTrue('member_two', user.username)
        user.membership.bill_day = two_weeks_ago.day
        user.membership.set_to_package(self.advocatePackage, start_date=two_weeks_ago)
        self.assertTrue(user.membership.package_name() != None)
        self.assertEqual('Advocate', user.membership.package_name())

        # Generate bill at start of membership
        run_bills = user.membership.generate_bills(target_date=today)
        self.assertEqual(1, len(run_bills['member_two']['line_items']))
        bill_today = user.bills.get(period_start=two_weeks_ago)
        self.assertEqual(two_weeks_ago, bill_today.due_date)

        # Generate the next month's bill
        next_start_date = user.membership.next_period_start()
        user.membership.generate_bills(target_date=next_start_date)
        next_bill = user.bills.get(period_start=next_start_date)
        self.assertEqual(next_start_date, next_bill.due_date)
        self.assertTrue(next_bill.amount == bill_today.amount)
        self.assertEqual(30, next_bill.amount)

    def test_new_user_new_membership_with_end_date(self):
        user = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.assertEqual('member_three', user.username)
        self.assertFalse(user.membership.package_name() != None)

        # Set end date one month from now
        end = one_month_from_now - timedelta(days=1)

        user.membership.bill_day = today.day
        self.assertEqual(today.day, user.membership.bill_day)
        user.membership.set_to_package(self.pt10Package, start_date=today, end_date=end)
        self.assertEqual(10, user.membership.allowance_by_resource(Resource.objects.day_resource))
        self.assertTrue(user.membership.end_date != None)

        # No bill generated the previous month
        run_last_months_bill = user.membership.generate_bills(target_date = one_month_ago)
        self.assertEqual(None, run_last_months_bill)

        # Test for current bill
        run_current_bills = user.membership.generate_bills(target_date=today)
        self.assertEqual(1, len(run_current_bills['member_three']['line_items']))
        current_bill = user.bills.get(period_start=today)
        self.assertEqual(today, current_bill.due_date)
        self.assertTrue(current_bill.amount == 180)

        # Due to end_date, there should be no bill next month
        run_next_month_bill = user.membership.generate_bills(target_date=one_month_from_now)
        self.assertTrue(run_next_month_bill == None)

    def test_backdated_new_membership_with_end_date(self):
        # Membership start date of two weeks ago and ending in two weeks
        start = two_weeks_ago
        end = (start + relativedelta(months=1)) - timedelta(days=1)
        user = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        self.assertEqual('member_four', user.username)
        self.assertTrue(user.membership.package_name() == None)

        # Start PT5 membership two weeks ago
        user.membership.bill_day = start.day
        user.membership.set_to_package(self.pt5Package, start_date=start, end_date=end)
        self.assertTrue(user.membership.package_name() == 'PT5')
        self.assertEqual(5, user.membership.allowance_by_resource(Resource.objects.day_resource))

        # No bill for previous month since there was no membership
        run_prev_bill = user.membership.generate_bills(target_date=one_month_ago)
        self.assertEqual(None, run_prev_bill)

        # Test current bill
        run_current_bill = user.membership.generate_bills(target_date=start)
        current_bill = user.bills.get(period_start=start)
        self.assertEqual(100, current_bill.amount)
        self.assertEqual(1, current_bill.line_items.all().count())

        # No bill for next month since there is end date at end of bill period
        run_next_bill = user.membership.generate_bills(target_date=one_month_from_now)
        self.assertEqual(None, run_next_bill)

    def test_new_membership_package_paid_by_other_member(self):
        user = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        payer = self.user1
        self.assertTrue(user.membership.package_name() == None)
        payer.membership.bill_day = 12

        # Payer has no active subscriptions
        self.assertEqual(0, payer.membership.active_subscriptions().count())

        # Set Resident membership package for user to be paid by another member 'payer'
        user.membership.bill_day = today.day
        user.membership.set_to_package(self.residentPackage, start_date=today, paid_by=payer)
        self.assertTrue(user.membership.package_name() == 'Resident')
        users_subscriptions = user.membership.active_subscriptions()

        # Test that payer pays for each of the 3 active subscriptions for user
        self.assertTrue(3, users_subscriptions.count())
        for u in users_subscriptions:
            self.assertEqual(u.paid_by, payer)

        # Generate bills and 0 for user, but 1 for payer
        run_user_bill = user.membership.generate_bills(target_date=today)
        user_bill = UserBill.objects.filter(user=user).count()
        self.assertEqual(0, user_bill)
        payer_bill = payer.bills.get(period_start = today)
        self.assertTrue(payer_bill.package_name == 'Resident')
        self.assertTrue(payer_bill.amount == 395)

        # Bill is for user membership and not that of payer
        self.assertTrue(payer_bill.membership.id == user.membership.id)

    def test_new_t40_team_member(self):
        # Creat team lead with T40 package
        team_lead = User.objects.create(username='Team_Lead', first_name='Team', last_name='Lead')
        team_lead.membership.bill_day = today.day
        team_lead.membership.set_to_package(self.t40Package, start_date=one_month_ago)
        self.assertTrue('T40' == team_lead.membership.package_name())

        user = User.objects.create(username='Member_Six', first_name='Member', last_name='Six')
        user.membership.bill_day = today.day
        self.assertTrue(user.membership.bill_day is not None)
        user.membership.set_to_package(self.teamPackage, start_date=today, paid_by=team_lead)
        self.assertEqual(0, user.membership.allowance_by_resource(Resource.objects.day_resource))
        users_subscriptions = user.membership.active_subscriptions()

        # Test that payer pays for each of the 3 active subscriptions for user
        self.assertTrue(1, users_subscriptions.count())
        for u in users_subscriptions:
            self.assertEqual(u.paid_by, team_lead)

        # Test bill is for team_lead and not user for $720
        run_user_bill = user.membership.generate_bills(target_date=today)
        team_lead.membership.generate_bills(target_date=today)
        self.assertEqual(1, len(run_user_bill))
        team_lead_bill = team_lead.bills.filter(period_start=today)
        print_all_bills(team_lead)
        self.assertEquals(2, len(team_lead_bill))
        total = 0
        for b in team_lead_bill:
            total = total + b.amount
        self.assertEqual(720, total)

    def test_alter_future_subscriptions(self):
        start = one_week_from_now
        user = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
        user.membership.bill_day = start.day
        self.assertEqual('Member', user.first_name)

        # Set membership package of PT5 to start in one week
        user.membership.set_to_package(self.pt5Package, start_date=start)
        self.assertTrue(len(user.membership.active_subscriptions()) == 0)

        # Test no current bill but future bill will be for $100
        bill_today = user.membership.generate_bills(target_date=today)
        self.assertTrue(bill_today is None)
        user.membership.generate_bills(target_date=start)
        start_date_bill = user.bills.get(period_start=start)
        self.assertEqual(100, start_date_bill.amount)
        self.assertEqual(1, start_date_bill.line_items.all().count())

        # Add key to future membership plan
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=user.membership, package_name='PT5', allowance=1, start_date=start, monthly_rate=100, overage_rate=0)
        future_subs = user.membership.active_subscriptions(target_date=start)
        self.assertEqual(2, len(future_subs))
        self.assertTrue(ResourceSubscription.objects.get(resource=Resource.objects.key_resource) in future_subs)

        # Run bill for start date again and test to make sure it will be $200
        user.membership.generate_bills(target_date=start)
        bill_with_key = user.bills.get(period_start=start)
        self.assertEqual(200, bill_with_key.amount)
        self.assertEqual(2, bill_with_key.line_items.all().count())
        self.assertTrue(user.membership.generate_bills(target_date=one_month_from_now + timedelta(days=7)) is not None)

    def test_returning_member_with_future_subscriptions_and_end_dates(self):
        user = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')

        # Start membership package in one week for a length of 2 weeks
        start = one_week_from_now
        end = start + relativedelta(weeks=2)
        user.membership.bill_day = start.day
        self.assertTrue(user.membership.package_name() is None)
        user.membership.set_to_package(self.advocatePackage, start_date=start, end_date=end)

        # Test that subscription starts in a week and then ends 2 weeks later
        self.assertTrue(len(user.membership.active_subscriptions()) == 0)
        self.assertTrue(len(user.membership.active_subscriptions(target_date=start)) is 1)
        self.assertTrue(len(user.membership.active_subscriptions(target_date=one_month_from_now)) is 0)

        # Test bills
        bill_today = user.membership.generate_bills(target_date=today)
        self.assertTrue(bill_today is None)
        user.membership.generate_bills(target_date=start)
        bill_on_start_date = user.bills.get(period_start=start)
        self.assertTrue(bill_on_start_date is not None)
        print_bill(bill_on_start_date)
        # TODO: Do we want this prorated or not???
        # self.assertEqual(bill_on_start_date.amount, 30)

    def test_current_pt5_adds_key(self):
        #Create user with PT5 membership package started 2 months ago
        user = User.objects.create(username='member_nine', first_name='Member', last_name='Nine')
        user.membership.bill_day = today.day
        user.membership.set_to_package(self.pt5Package, start_date=two_months_ago)

        # Confirm last month's bill for PT5
        start = today
        user.membership.generate_bills(target_date=one_month_ago)
        last_months_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(100, last_months_bill.amount)
        self.assertEqual('PT5', last_months_bill.membership.package_name())

        # Add key subscription today
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=user.membership, package_name='PT5', allowance=1, start_date=start, monthly_rate=100, overage_rate=0)
        self.assertTrue(len(user.membership.active_subscriptions()) is 2)
        self.assertTrue(ResourceSubscription.objects.get(resource=Resource.objects.key_resource) in user.membership.active_subscriptions())

        # Test new bill is $200 for PT5 with key
        user.membership.generate_bills(target_date=start)
        current_bill = user.bills.get(period_start=start)
        self.assertEqual(200, current_bill.amount)
        self.assertTrue(current_bill.line_items.all().count() is 2)

    def test_resident_adds_5_coworking_days_today(self):
        #Create user with Residet membership package started 2 months ago
        user = User.objects.create(username='member_ten', first_name='Member', last_name='Ten')
        user.membership.bill_day = today.day
        user.membership.set_to_package(self.residentPackage, start_date=two_months_ago)

        # self.assertIn(Resource.objects.day_resource, user.membership.active_subscriptions())
        day_subscription = ResourceSubscription.objects.get(membership=user.membership, resource=Resource.objects.day_resource)
        day_subscription
        self.assertEqual(5, day_subscription.allowance)

        # Test previous bill to be $395
        user.membership.generate_bills(target_date=one_month_ago)
        past_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(395, past_bill.amount)

        # Change coworking day subscription from 5 to 10
        day_subscription.end_date = today - timedelta(days=1)
        day_subscription.save()
        self.assertFalse(day_subscription.end_date is None)
        ResourceSubscription.objects.create(resource=Resource.objects.day_resource, membership=user.membership, package_name='Resident', allowance=10, start_date=today, monthly_rate=0, overage_rate=0)
        new_day_subscription = ResourceSubscription.objects.get(membership=user.membership, resource=Resource.objects.day_resource, end_date=None)
        self.assertEqual(10, new_day_subscription.allowance)

        # Test billing
        user.membership.generate_bills(target_date=today)
        current_bill = user.bills.get(period_start=today)
        self.assertEqual(395, current_bill.amount)
        self.assertTrue(current_bill.line_items.all().count() is 2)
        user.membership.generate_bills(target_date=one_month_from_now)
        future_bill = user.bills.get(period_start=one_month_from_now)
        self.assertEqual(395, future_bill.amount)

    


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
