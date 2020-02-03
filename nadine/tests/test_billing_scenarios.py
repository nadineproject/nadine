import traceback, logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, override_settings
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.billing import BillingBatch, UserBill, Payment
from nadine.models.membership import MembershipPackage, SubscriptionDefault
from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.organization import Organization
from nadine.models.resource import Resource, Room
from nadine.models.usage import CoworkingDay, Event


today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_week_from_now = today + timedelta(days=7)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)
two_weeks_ago = today - timedelta(days=14)
two_weeks_from_now = today + timedelta(days=14)
two_months_from_now = today + relativedelta(months=2)

def print_all_bills(user):
    for bill in UserBill.objects.filter(user=user):
        print_bill(bill)

def print_bill(bill):
    print(("UserBill %d" % bill.id))
    print(("  user: %s" % bill.user))
    print(("  due_date: %s" % bill.due_date))
    print(("  period_start: %s" % bill.period_start))
    print(("  period_end: %s" % bill.period_end))
    if bill.is_closed:
        print(("  closed_ts: %s" % bill.closed_ts))
    print(("  amount: $%s" % bill.amount))
    print("  line_items:")
    for line_item in bill.line_items.all().order_by('id'):
        print(("    %s: $%s" % (line_item.description, line_item.amount)))


@override_settings(SUSPEND_MEMBER_ALERTS=True)
class BillingTestCase(TestCase):

    def setUp(self):
        # Turn on logging for nadine models
        # logging.getLogger('nadine.models').setLevel(logging.DEBUG)
        logging.getLogger('nadine.models').setLevel(logging.INFO)

        # Advocate Package
        self.advocatePackage = MembershipPackage.objects.create(name='Advocate')
        SubscriptionDefault.objects.create(
            package=self.advocatePackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 30,
            overage_rate = 20,
        )

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

        #PT10 Package
        self.pt10Package = MembershipPackage.objects.create(name="PT10")
        SubscriptionDefault.objects.create(
            package = self.pt10Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 180,
            allowance = 10,
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

        #T20 Package
        self.t20Package = MembershipPackage.objects.create(name="T20")
        SubscriptionDefault.objects.create(
            package = self.t20Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 360,
            allowance = 20,
            overage_rate = 20
        )

        #T20 Package
        self.t40Package = MembershipPackage.objects.create(name="T40")
        SubscriptionDefault.objects.create(
            package = self.t40Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 720,
            allowance = 40,
            overage_rate = 20
        )

        #Team Package
        self.teamPackage = MembershipPackage.objects.create(name="Team")
        SubscriptionDefault.objects.create(
            package = self.teamPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 0,
            allowance = 0,
            overage_rate = 0
        )

        #Event Package
        self.eventPackage = MembershipPackage.objects.create(name='Events')
        SubscriptionDefault.objects.create(
            package = self.eventPackage,
            resource = Resource.objects.event_resource,
            monthly_rate = 100,
            allowance = 10,
            overage_rate = 20
        )

    def test_drop_in_on_billing_date_is_associated_with_correct_bill(self):
        # PT-5 5/20/2010 - 6/19/2010 & Basic since 6/20/2010
        # Daily activity 6/11/2010 through 6/25/2010
        user = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')
        membership = Membership.objects.for_user(user)
        membership.bill_day = 20
        membership.save()
        membership.set_to_package(self.pt5Package, start_date=date(2010, 5, 20), end_date=date(2010, 6, 19))
        membership.set_to_package(self.basicPackage, start_date=date(2010, 6, 20))
        days = {}
        for day in range(11, 25):
            visit_date = date(2010, 6, day)
            days[visit_date] = CoworkingDay.objects.create(user=user, visit_date=visit_date, payment='Bill')

        # Run the billing batch
        batch = BillingBatch.objects.run(start_date=date(2010, 5, 20), end_date=date(2010, 7, 20))
        self.assertTrue(batch.successful)
        self.assertEqual(3, batch.bills.count())

        # May 20th bill = PT5 with 9 days
        # Total = $75 + 4 * $20 = $155
        self.assertEqual(membership.matching_package(date(2010, 5, 20)), self.pt5Package)
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
        user6_membership = Membership.objects.for_user(user6)
        user6_membership.set_to_package(self.pt5Package, start_date=date(2008, 1, 1), end_date=None, bill_day=1)
        user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
        user7_membership = Membership.objects.for_user(user7)
        user7_membership.set_to_package(self.pt5Package, start_date=date(2008, 1, 1), paid_by=user6, bill_day=1)
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
        self.assertEqual(270, user6.profile.outstanding_amount)
        self.assertEqual(0, user7.profile.outstanding_amount)
        self.assertEqual(0, user8.profile.outstanding_amount)

    def test_change_bill_day(self):
        # PT5 from 1/10/2010 billed on the 10th
        user = User.objects.create(username='test_user', first_name='Test', last_name='User')
        membership = Membership.objects.for_user(user)
        membership.bill_day = 10
        membership.set_to_package(self.pt5Package, start_date=date(2010, 1, 10))
        self.assertEqual(10, membership.bill_day)

        # Three days of activity on 5/9, 5/15, and 6/2
        day1 = CoworkingDay.objects.create(user=user, visit_date=date(2010, 5, 9), payment='Bill')
        day2 = CoworkingDay.objects.create(user=user, visit_date=date(2010, 5, 15), payment='Bill')
        day3 = CoworkingDay.objects.create(user=user, visit_date=date(2010, 6, 2), payment='Bill')

        # Generate bills for the three days we created
        batch = BillingBatch.objects.run(start_date=date(2010, 5, 9), end_date=date(2010, 6, 2))
        self.assertTrue(batch.successful)
        self.assertEqual(2, batch.bills.count())
        print_all_bills(user)

        # Day 1 ended up on April 10th bill
        april_10_bill = user.bills.get(period_start=date(2010, 4, 10))
        self.assertTrue(day1 in april_10_bill.coworking_days())
        self.assertFalse(day2 in april_10_bill.coworking_days())
        self.assertFalse(day3 in april_10_bill.coworking_days())
        # Days 2 and 3 ended up on May 10th bill
        may_10_bill = user.bills.get(period_start=date(2010, 5, 10))
        self.assertFalse(day1 in may_10_bill.coworking_days())
        self.assertTrue(day2 in may_10_bill.coworking_days())
        self.assertTrue(day3 in may_10_bill.coworking_days())

        # April bill is closed, May bill is still open
        self.assertTrue(april_10_bill.is_closed)
        self.assertTrue(may_10_bill.is_open)

        # Change the bill date to the 1st
        membership.change_bill_day(date(2010, 6, 1))
        self.assertEqual(1, membership.bill_day)

        # Generate the bills again
        batch = BillingBatch.objects.run(start_date=date(2010, 5, 1), end_date=date(2010, 6, 2))
        self.assertTrue(batch.successful)
        self.assertEqual(1, batch.bills.count())
        print_all_bills(user)

        # Make sure the 6/2 day got on the new June bill
        june_1_bill = user.bills.get(period_start=date(2010, 6, 1))
        self.assertFalse(day1 in june_1_bill.coworking_days())
        self.assertFalse(day2 in june_1_bill.coworking_days())
        self.assertTrue(day3 in june_1_bill.coworking_days())


    def test_start_package(self):
        #New user joins and starts a PT5 membership the same day
        user = User.objects.create(username='member_one', first_name='Member', last_name='One')
        membership = Membership.objects.for_user(user)
        membership.bill_day = 1
        membership.set_to_package(self.pt5Package, start_date=date(2017, 6, 1))
        self.assertEqual(1, membership.bill_day)
        self.assertEqual(5, membership.allowance_by_resource(resource=1))
        self.assertEqual('PT5', membership.package_name())

        # Generate the bill at start
        batch = BillingBatch.objects.run(start_date=date(2017, 6, 1), end_date=date(2017, 7, 1))
        self.assertTrue(batch.successful)
        july_bill = user.bills.get(period_start=date(2017, 7, 1))
        print_bill(july_bill)
        self.assertTrue(july_bill != None)
        self.assertEqual(75, july_bill.amount)

    def test_backdated_new_user_and_membership(self):
        # New user starts Advocate membership backdated 2 weeks
        user = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        membership = Membership.objects.for_user(user)
        membership.bill_day = two_weeks_ago.day
        membership.save()
        membership.set_to_package(self.advocatePackage, start_date=two_weeks_ago)
        self.assertEqual('Advocate', membership.package_name())
        next_start_date = membership.next_period_start()

        # Generate bill at start of membership
        batch = BillingBatch.objects.run(start_date=two_weeks_ago, end_date=two_weeks_ago)
        self.assertTrue(batch.successful)
        bill_today = user.bills.get(period_start=two_weeks_ago)
        self.assertEqual(30, bill_today.amount)
        self.assertTrue((membership.next_period_start() - timedelta(days=1)) == bill_today.due_date)
        self.assertTrue(bill_today.is_open)

        # Generate the next month's bill
        batch = BillingBatch.objects.run(start_date=next_start_date, end_date=next_start_date)
        self.assertTrue(batch.successful)
        next_bill = user.bills.get(period_start=next_start_date)
        self.assertTrue(next_bill.amount == bill_today.amount)
        self.assertEqual(30, next_bill.amount)

    def test_new_user_new_membership_with_end_date(self):
        user = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        membership = Membership.objects.for_user(user)
        self.assertFalse(membership.package_name() != None)

        # Set end date one month from now
        end = one_month_from_now - timedelta(days=1)

        membership.bill_day = today.day
        self.assertEqual(today.day, membership.bill_day)
        membership.set_to_package(self.pt10Package, start_date=today, end_date=end)
        self.assertEqual(10, membership.allowance_by_resource(Resource.objects.day_resource))
        self.assertTrue(membership.end_date != None)

        # No bill generate the previous month
        last_months_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(last_months_batch.successful)
        self.assertTrue(0 == len(user.bills.filter(period_start=one_month_ago)))

        # Test for current bill
        end_of_this_period = one_month_from_now - timedelta(days=1)
        current_month_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(current_month_batch.successful)
        current_bill = user.bills.get(period_start=today)
        self.assertEqual(end_of_this_period, current_bill.due_date)
        self.assertTrue(current_bill.amount == 180)

        # Due to end_date, there should be no bill next month
        run_next_month_batch = BillingBatch.objects.run(start_date=one_month_from_now, end_date=one_month_from_now)
        self.assertTrue(len(user.bills.filter(period_start=one_month_from_now)) == 0)

    def test_backdated_new_membership_with_end_date(self):
        # Membership start date of two weeks ago and ending in two weeks
        start = two_weeks_ago
        end = (start + relativedelta(months=1)) - timedelta(days=1)
        user = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        membership = Membership.objects.for_user(user)
        self.assertTrue(membership.package_name() == None)

        # Start PT5 membership two weeks ago
        membership.bill_day = start.day
        membership.set_to_package(self.pt5Package, start_date=start, end_date=end)
        self.assertTrue(membership.package_name() == 'PT5')
        self.assertEqual(5, membership.allowance_by_resource(Resource.objects.day_resource))

        # No previous bill since there was no membership
        run_last_month_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(len(user.bills.filter(period_start=one_month_ago)) == 0)

        # Test Current Bill
        current_batch = BillingBatch.objects.run(start_date=start, end_date=end)
        current_bill = user.bills.get(period_start=start)
        self.assertEqual(75, current_bill.amount)
        self.assertEqual(1, current_bill.line_items.all().count())

        # Test next months bill
        next_months_batch = BillingBatch.objects.run(start_date=end, end_date=one_month_from_now)
        self.assertTrue(0 == len(user.bills.filter(period_start=one_month_from_now)))

    def test_new_membership_package_paid_by_other_member(self):
        user = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        payer = User.objects.create(username='member_nine', first_name='Member', last_name='Nine')
        membership = Membership.objects.for_user(user)
        payer_membership = Membership.objects.for_user(payer)

        # Payer's bill date is the 12th and has no active subscriptions
        payer_membership.bill_day = 12
        payer_membership.save()
        self.assertEqual(0, payer_membership.active_subscriptions().count())

        # Set Resident membership package for user to be paid by another member 'payer'
        membership.bill_day = 15
        membership.save()
        self.assertEqual(membership.package_name(), None)
        membership.set_to_package(self.residentPackage, start_date=date(2010, 6, 15), paid_by=payer)
        self.assertEqual(membership.package_name(), 'Resident')
        self.assertEqual(membership.bill_day, 15)

        # Test that payer pays for each of the 3 active subscriptions for user
        users_subscriptions = membership.active_subscriptions()
        self.assertEqual(2, users_subscriptions.count())
        for u in users_subscriptions:
            self.assertEqual(u.paid_by, payer)
        print(users_subscriptions)

        # Generate the bills from the 12th through the 15th
        run_bill_batch = BillingBatch.objects.run(start_date=date(2010, 6, 12), end_date=date(2010, 6, 15))
        self.assertTrue(run_bill_batch.successful)
        # Generate bills and check there are 0 for user, but 1 for payer
        self.assertEqual(0, user.bills.count())
        self.assertEqual(1, payer.bills.count())

        print_all_bills(payer)
        payer_bill = payer.bills.get(period_start=date(2010, 6, 15))
        for s in payer_bill.subscriptions():
            self.assertEqual('Resident', s.package_name)
            # Bill is for user membership and not that of payer
            self.assertFalse(payer_membership.id == s.membership.id)
            self.assertEqual(membership.id, s.membership.id)

    def test_new_t40_team_member(self):
        # Creat team lead with T40 package
        team_lead = User.objects.create(username='Team_Lead', first_name='Team', last_name='Lead')
        lead_membership = Membership.objects.for_user(team_lead)
        lead_membership.bill_day = today.day
        lead_membership.set_to_package(self.t40Package, start_date=one_month_ago)
        self.assertTrue('T40' == lead_membership.package_name())

        user = User.objects.create(username='Member_Test', first_name='Member', last_name='Test')
        user_membership = Membership.objects.for_user(user)
        user_membership.bill_day = today.day
        self.assertTrue(user_membership.bill_day is not None)
        user_membership.set_to_package(self.teamPackage, start_date=today, paid_by=team_lead)
        self.assertEqual(0, user_membership.allowance_by_resource(Resource.objects.day_resource))
        users_subscriptions = user_membership.active_subscriptions()

        # Test that payer pays for each of the 3 active subscriptions for user
        self.assertTrue(1, users_subscriptions.count())
        for u in users_subscriptions:
            self.assertEqual(u.paid_by, team_lead)

        # Test bill is for team_lead and not user for $720
        current_bill_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(current_bill_batch.successful)
        team_lead_bill = team_lead.bills.filter(period_start=today)
        self.assertEqual(1, len(team_lead_bill))
        total = 0
        for b in team_lead_bill:
            total = total + b.amount
        self.assertEqual(720, total)

    def test_alter_future_subscriptions(self):
        start = one_week_from_now
        end_of_this_period = start + relativedelta(months=1) - timedelta(days=1)
        user = User.objects.create(username='member_future', first_name='Member', last_name='Future')

        # Set membership package of PT5 to start in one week
        membership = Membership.objects.for_user(user)
        membership.bill_day = start.day
        membership.set_to_package(self.pt5Package, start_date=start)
        self.assertEqual(0, membership.active_subscriptions().count())

        # Test no current bill but future bill will be for $75
        todays_bill_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(todays_bill_batch.successful)
        self.assertEqual(0, todays_bill_batch.bills.count())
        self.assertEqual(0, user.bills.count())
        future_bill_batch = BillingBatch.objects.run(start_date=start, end_date=start)
        self.assertTrue(future_bill_batch.successful)
        self.assertEqual(1, future_bill_batch.bills.count())
        future_bill = user.bills.get(period_start=start)
        self.assertEqual(75, future_bill.amount)
        self.assertEqual(1, future_bill.line_items.count())

        # Add key to future membership plan
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership,  allowance=1, start_date=start, monthly_rate=100, overage_rate=0)
        self.assertEqual(2, membership.active_subscriptions(target_date=start).count())
        self.assertTrue(membership.has_key(target_date=start))

        # Run bill for start date again and test to make sure it will be $175
        altered_batch = BillingBatch.objects.run(start_date=start, end_date=start)
        self.assertTrue(altered_batch.successful)
        self.assertEqual(1, altered_batch.bills.count())
        bill_with_key = user.bills.get(period_start=start)
        self.assertEqual(175, bill_with_key.amount)
        self.assertEqual(2, bill_with_key.line_items.count())

    def test_returning_member_with_future_subscriptions_and_end_dates(self):
        user = User.objects.create(username='member_returning', first_name='Member', last_name='Returning')
        membership = Membership.objects.for_user(user)

        # Start membership package in one week for a length of 2 weeks
        start = date(2010, 6, 7)
        end = date(2010, 6, 21)
        membership.bill_day = start.day
        self.assertTrue(membership.package_name() is None)
        membership.set_to_package(self.advocatePackage, start_date=start, end_date=end)

        # Test that subscription starts in a week and then ends 2 weeks later
        self.assertTrue(len(membership.active_subscriptions()) == 0)
        self.assertTrue(len(membership.active_subscriptions(target_date=start)) is 1)
        self.assertTrue(len(membership.active_subscriptions(target_date=one_month_from_now)) is 0)

        # Test bills
        todays_bill_batch = BillingBatch.objects.run(start_date=date(2010, 6, 1), end_date=date(2010, 6, 1))
        self.assertTrue(todays_bill_batch.successful)
        self.assertTrue(0 == len(user.bills.filter(period_start=today)))
        batch_on_start_date = BillingBatch.objects.run(start_date=start, end_date=end - timedelta(days=1))
        self.assertTrue(batch_on_start_date.successful)
        start_date_bill = user.bills.get(period_start=start)
        self.assertTrue(start_date_bill is not None)
        # Bill should be prorated
        self.assertTrue(start_date_bill.amount < self.advocatePackage.monthly_rate())

    def test_current_pt5_adds_key(self):
        #Create user with PT5 membership package started 2 months ago
        user = User.objects.create(username='member_pt5', first_name='Member', last_name='PT5')
        membership = Membership.objects.for_user(user)
        membership.bill_day = today.day
        membership.set_to_package(self.pt5Package, start_date=two_months_ago)

        #Confirm last month's bill for PT5
        start = today
        last_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=yesterday)
        last_months_bill = user.bills.get(period_start=one_month_ago)
        self.assertTrue(last_batch.successful)
        self.assertEqual(75, last_months_bill.amount)
        for s in last_months_bill.subscriptions():
            self.assertEqual('PT5', s.package_name)

        # Add key subscription today
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership, package_name='PT5', allowance=1, start_date=start, monthly_rate=100, overage_rate=0)
        self.assertTrue(len(membership.active_subscriptions()) is 2)
        self.assertTrue(ResourceSubscription.objects.get(resource=Resource.objects.key_resource) in membership.active_subscriptions())

        # Test new bill is $175 for PT5 with key
        adjusted_batch = BillingBatch.objects.run(start_date=start, end_date=start)
        self.assertTrue(adjusted_batch.successful)
        current_bill = user.bills.get(period_start=start)
        self.assertEqual(175, current_bill.amount)
        self.assertTrue(current_bill.line_items.all().count() is 2)

    def test_resident_adds_5_coworking_days_today(self):
        #Create user with Residet membership package started 2 months ago
        user = User.objects.create(username='member_ten', first_name='Member', last_name='Ten')
        membership = Membership.objects.for_user(user)
        membership.bill_day = today.day
        membership.set_to_package(self.residentPackage, start_date=two_months_ago)
        day_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.day_resource)
        day_subscription
        self.assertEqual(5, day_subscription.allowance)

        # Test previous bill to be $475
        previous_bill_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(previous_bill_batch.successful)
        past_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(475, past_bill.amount)

        # Change coworking day subscription from 5 to 10
        day_subscription.end_date = today - timedelta(days=1)
        day_subscription.save()
        self.assertFalse(day_subscription.end_date is None)
        ResourceSubscription.objects.create(resource=Resource.objects.day_resource, membership=membership, package_name='Resident', allowance=10, start_date=today, monthly_rate=0, overage_rate=0)
        new_day_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.day_resource, end_date=None)
        self.assertTrue(len(membership.active_subscriptions()) is 2)
        self.assertEqual(10, new_day_subscription.allowance)

        # Test billing with updated subscriptions
        todays_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(todays_batch.successful)
        self.assertTrue(todays_batch.bills.count() == 1)
        current_bill = user.bills.get(period_start=today)
        self.assertEqual(475, current_bill.amount)
        self.assertTrue(current_bill.line_items.all().count() is 2)

        future_batch = BillingBatch.objects.run(start_date=one_month_from_now, end_date=one_month_from_now)
        self.assertEqual(1, future_batch.bills.count())
        future_bill = user.bills.get(period_start=one_month_from_now)
        self.assertEqual(475, future_bill.amount)

    def test_team_lead_changes_package(self):
        # Create user with t40 package started 2 months ago
        lead = User.objects.create(username='member_fourteen', first_name='Member', last_name='Fourteen')
        lead_membership = Membership.objects.for_user(lead)
        lead_membership.bill_day = today.day
        lead_membership.set_to_package(self.t40Package, start_date=two_months_ago)

        # Create team membership
        team_1 = User.objects.create(username='member_fifteen', first_name='Member', last_name='Fifteen')
        team_1_membership = Membership.objects.for_user(team_1)
        team_1_membership.bill_day = today.day
        team_1_membership.set_to_package(self.teamPackage, start_date=two_months_ago, paid_by=lead)
        team_2 = User.objects.create(username='member_sixteen', first_name='Member', last_name='Sixteen')
        team_2_membership = Membership.objects.for_user(team_2)
        team_2_membership.bill_day = today.day
        team_2_membership.set_to_package(self.teamPackage, start_date=two_months_ago, paid_by=lead)

        # Generate Bills for lead for one month ago
        # Should be 720 with 3 line items under the lead's billing
        last_months_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(last_months_batch.successful)
        self.assertEqual(1, last_months_batch.bills.count())
        lead_original_bills = UserBill.objects.get(user=lead)
        self.assertEqual(3, lead_original_bills.line_items.count())
        self.assertEqual(720, lead_original_bills.amount)

        # Change lead's membership packge to T20 and check billing
        lead_membership.end_all()
        lead_membership.set_to_package(self.t20Package, start_date=today)
        self.assertTrue('T20' == lead_membership.package_name())

        #Should have bill with 3 line items and a total of $360
        updated_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        lead_new_bills = UserBill.objects.get(user=lead, period_start=today)
        self.assertEqual(3, lead_new_bills.line_items.count())
        self.assertEqual(360, lead_new_bills.amount)

    def test_team_lead_ends_package(self):
        # Create user with t40 package started 2 months ago
        lead = User.objects.create(username='member_seventeen', first_name='Member', last_name='Seventeen')
        lead_membership = Membership.objects.for_user(lead)
        lead_membership.bill_day = today.day
        lead_membership.set_to_package(self.t20Package, start_date=two_months_ago)

        # Create team membership
        team_1 = User.objects.create(username='member_eighteen', first_name='Member', last_name='Eighteen')
        team_1_membership = Membership.objects.for_user(team_1)
        team_1_membership.bill_day = today.day
        team_1_membership.set_to_package(self.teamPackage, start_date=two_months_ago, paid_by=lead)
        resident = User.objects.create(username='member_nineteen', first_name='Member', last_name='Nineteen')
        resident_membership = Membership.objects.for_user(resident)
        resident_membership.bill_day = today.day
        resident_membership.set_to_package(self.residentPackage, start_date=two_months_ago, paid_by=lead)

        # Generate last months bills
        # Test for total of 360 + 0 + 475 = $835
        last_months_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(last_months_batch.successful)
        lead_original_bills = UserBill.objects.get(user=lead)
        self.assertEqual(4, lead_original_bills.line_items.count())
        self.assertEqual(835, lead_original_bills.amount)

        # End lead and team members' subscriptions but keep resident
        lead_membership.end_all()
        team_1_membership.end_all()

        # Lead and team member should have 0 active_subscriptions while Resident has 2
        self.assertEqual(0, lead_membership.active_subscriptions().count())
        self.assertEqual(0, team_1_membership.active_subscriptions().count())
        self.assertEqual(2, resident_membership.active_subscriptions().count())

        # Rerun billing - should only be $475 for the resident paid by lead
        updated_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(updated_batch.successful)
        lead_new_bills = UserBill.objects.get(user=lead, period_start=today)
        self.assertEqual(475, lead_new_bills.amount)

    def test_pt10_adds_key_next_bill_period(self):
        # Create user with PT10 package started 2 months ago
        user = User.objects.create(username='member_twenty', first_name='Member', last_name='Twenty')
        membership = Membership.objects.for_user(user)
        membership.bill_day = today.day
        membership.set_to_package(self.pt10Package, start_date=two_months_ago)
        self.assertTrue('PT10' == membership.package_name())

        # Generate last month's bills
        # Should have one bill for user for $180
        last_months_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(last_months_batch.successful)
        last_months_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(180, last_months_bill.amount)

        # Add key subscription
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership, package_name='PT10', allowance=1, start_date=today, monthly_rate=100, overage_rate=0)
        self.assertEqual(2, membership.active_subscriptions().count())
        day_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.day_resource)
        day_subscription
        self.assertEqual(10, day_subscription.allowance)

        # Generate new bill with the key
        # Should be for $280 = 100 + 180
        new_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(new_batch.successful)
        user_bill_with_key = user.bills.get(period_start=today)
        self.assertTrue(user_bill_with_key.amount == 280)

        # Generate next month's bill
        next_batch = BillingBatch.objects.run(start_date=one_month_from_now, end_date=one_month_from_now)
        self.assertTrue(next_batch.successful)
        bill_next_month = user.bills.get(period_start=one_month_from_now)
        self.assertTrue(bill_next_month.amount == 280)

    def test_pt10_adds_key_halfway_through_bill_period(self):
        # Create user with PT10 package started 2 weeks ago
        user = User.objects.create(username='member_twentyone', first_name='Member', last_name='Twentyone')
        membership = Membership.objects.for_user(user)
        membership.bill_day = two_weeks_ago.day
        membership.set_to_package(self.pt10Package, start_date=two_weeks_ago)
        self.assertEqual('PT10', membership.package_name())
        self.assertEqual(1, membership.active_subscriptions().count())

        # Generate bill from 2 weeks ago
        # $180 for PT10 membership
        batch_from_two_weeks_ago = BillingBatch.objects.run(start_date=two_weeks_ago, end_date=two_weeks_ago)
        self.assertTrue(batch_from_two_weeks_ago.successful)
        last_months_bill = user.bills.get(period_start=two_weeks_ago)
        self.assertEqual(180, last_months_bill.amount)
        Payment.objects.create(bill=last_months_bill, user=user, amount=last_months_bill.amount, created_by=user)
        self.assertEqual(0, last_months_bill.total_owed)
        self.assertTrue(last_months_bill.is_open)

        # Add key subscription today
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership, package_name='PT10', allowance=1, start_date=today, monthly_rate=100, overage_rate=0)
        self.assertEqual(2, membership.active_subscriptions(today).count())

        # Generate bill with key
        # Total should be $180 + prorated key amount ($50-ish)
        new_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(new_batch.successful)
        bill_with_key = user.bills.get(period_start=two_weeks_ago)
        self.assertTrue(bill_with_key.total_owed == (bill_with_key.amount - 180))

    def test_change_some_end_dates_when_end_dates_already_exist(self):
        # Create user with Resident package with key started one month ago and end_date at end of next bill period_end
        start = one_month_ago
        end = (start + relativedelta(months=2)) - timedelta(days=1)
        user = User.objects.create(username='member_twentytwo', first_name='Member', last_name='Twentytwo')
        membership = Membership.objects.for_user(user)
        membership.bill_day = one_month_ago.day
        membership.set_to_package(self.residentPackage, start_date=start, end_date=end)
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership, package_name='Resident', allowance=1, start_date=start, end_date=end, monthly_rate=100, overage_rate=0)
        self.assertTrue('Resident' == membership.package_name())
        self.assertEqual(3, membership.active_subscriptions().count())
        self.assertTrue(len(membership.active_subscriptions(target_date=two_months_from_now)) == 0)

        # Generate bill at start date to check bills
        # $575 = 475 + 100
        start_date_batch = BillingBatch.objects.run(start_date=start, end_date=start)
        self.assertTrue(start_date_batch.successful)
        start_bill = user.bills.get(period_start=start)
        self.assertEqual(575, start_bill.amount)

        # Generate bill for after currently set end_date (should not exist)
        original_end_batch = BillingBatch.objects.run(start_date=two_months_from_now, end_date=two_months_from_now)
        self.assertTrue(original_end_batch.successful)
        original_end_bill = user.bills.filter(period_start=two_months_from_now)
        self.assertTrue(len(original_end_bill) == 0)

        # Change the end date everything except the key subscription
        for a in membership.active_subscriptions():
            if a.resource != Resource.objects.key_resource:
                a.end_date = yesterday
                a.save()
        key_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.key_resource)
        day_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.day_resource)
        desk_subscription = ResourceSubscription.objects.get(membership=membership, resource=Resource.objects.desk_resource)
        self.assertTrue(key_subscription.end_date == end)
        self.assertTrue(key_subscription.end_date != desk_subscription.end_date)
        self.assertTrue(key_subscription.end_date != day_subscription.end_date)
        self.assertTrue(desk_subscription.end_date == day_subscription.end_date)

        # Generate the bill for today to make bill of $100 for key subscription
        # Bill should total $100 with 1 line item
        new_today_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        new_today_bill = user.bills.get(period_start=today)
        self.assertEqual(100, new_today_bill.amount)
        self.assertTrue(membership.package_name() == 'Resident')
        self.assertEqual(1, new_today_bill.line_items.all().count())

        # Generate bill after end_date
        new_end_batch = BillingBatch.objects.run(start_date=two_months_from_now, end_date=two_months_from_now)
        self.assertTrue(new_end_batch.successful)
        new_end_bill = user.bills.filter(period_start=two_months_from_now)
        self.assertTrue(len(new_end_bill) == 0)

    def test_change_all_end_dates_when_end_dates_already_exist(self):
        # Create user with Resident package with key started one month ago and end_date at end of next bill period_end
        start = one_month_ago
        end = (start + relativedelta(months=2)) - timedelta(days=1)
        user = User.objects.create(username='member_twentythree', first_name='Member', last_name='Twentythree')
        membership = Membership.objects.for_user(user)
        membership.bill_day = one_month_ago.day
        membership.set_to_package(self.residentPackage, start_date=start, end_date=end)
        ResourceSubscription.objects.create(resource=Resource.objects.key_resource, membership=membership, package_name='Resident', allowance=1, start_date=start, end_date=end, monthly_rate=100, overage_rate=0)
        self.assertTrue('Resident' == membership.package_name())
        self.assertEqual(3, membership.active_subscriptions().count())
        self.assertTrue(len(membership.active_subscriptions(target_date=two_months_from_now)) == 0)

        # Generate bill for today to check bills
        # $575 = $475 (for Resident package) + $100 (for key)
        original_bill_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=yesterday)
        self.assertTrue(original_bill_batch.successful)
        original_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(575, original_bill.amount)

        # Generate bill for after currently set end_date (should not exist)
        original_end_batch = BillingBatch.objects.run(start_date=two_months_from_now, end_date=two_months_from_now)
        self.assertTrue(original_end_batch.successful)
        self.assertTrue(original_end_batch.bills.count() == 0)
        original_end_bill = user.bills.filter(period_start=two_months_from_now)

        # Set end resource subscriptions for yesterday
        membership.end_all(target_date = yesterday)
        self.assertTrue(membership.active_subscriptions().count() == 0)

        # There should now be no bill for today
        new_end_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(new_end_batch.successful)
        new_end_bill = user.bills.filter(period_start=today)
        self.assertTrue(len(new_end_bill) == 0)

    def test_ending_package_yesterday(self):
        # Create Advocate package with start date of one month ago
        start = one_month_ago
        user = User.objects.create(username='member_twentyfour', first_name='Member', last_name='Twentyfour')
        membership = Membership.objects.for_user(user)
        membership.bill_day = one_month_ago.day
        membership.set_to_package(self.advocatePackage, start_date=start)
        self.assertEqual(1, membership.active_subscriptions().count())

        # Generate today's bill if not end date
        original_bill_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=one_month_ago)
        self.assertTrue(original_bill_batch.successful)
        original_bill = user.bills.get(period_start=one_month_ago)
        self.assertEqual(30, original_bill.amount)

        # End all subscriptions yesterday
        membership.end_all(target_date=yesterday)
        self.assertTrue(membership.active_subscriptions().count() == 0)

        # Rerun billing now that subscriptions have been ended
        # There should be NO new bill to be paid
        ended_bill_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(ended_bill_batch.bills.count() == 0)
        self.assertTrue(ended_bill_batch.successful)
        new_end_bill = user.bills.filter(period_start=today)
        self.assertTrue(len(new_end_bill) == 0)

    def test_ending_package_at_end_of_bill_period(self):
        # Create PT10 package with start date of one month ago
        start = one_month_ago
        end = (today + relativedelta(months=1)) - timedelta(days=1)
        user = User.objects.create(username='member_twentyfive', first_name='Member', last_name='Twentyfive')
        membership = Membership.objects.for_user(user)
        membership.bill_day = one_month_ago.day
        membership.set_to_package(self.pt10Package, start_date=start)
        self.assertEqual(1, membership.active_subscriptions().count())

        # Generate today's bill
        original_bill_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(original_bill_batch.successful)
        original_bill = user.bills.get(period_start=today)
        self.assertEqual(180, original_bill.amount)

        # End all subscriptions at end of bill period and test still have active subscriptions today
        membership.end_all(target_date = end)
        self.assertTrue(membership.active_subscriptions().count() == 1)

        # Rerun billing now that subscriptions have been ended
        # Return one bill for $180
        ended_bill_batch = BillingBatch.objects.run(start_date=today, end_date=today)
        self.assertTrue(ended_bill_batch.successful)
        new_bill = user.bills.get(period_start=today)
        self.assertEqual(180, new_bill.amount)

        # There should be no future bill
        future_bill_batch = ended_bill_batch = BillingBatch.objects.run(start_date=one_month_from_now, end_date=one_month_from_now)
        end_bill = user.bills.filter(period_start=one_month_from_now)
        self.assertTrue(len(end_bill) == 0)

    def test_ending_package_today(self):
        # Create PT15 package with start date of one month ago with the next billing period starting tomorrow
        start = one_month_ago + timedelta(days=1)
        user = User.objects.create(username='member_twentysix', first_name='Member', last_name='Twentysix')
        membership = Membership.objects.for_user(user)
        membership.bill_day = start.day
        membership.set_to_package(self.pt15Package, start_date=start)
        self.assertEqual(1, membership.active_subscriptions().count())

        # Generate today's bill if not end date
        today_bill_batch = BillingBatch.objects.run(start_date=start, end_date=start)
        self.assertTrue(today_bill_batch.successful)
        original_bill = user.bills.get(period_start=start)
        self.assertEqual(225, original_bill.amount)

        # Set end date to today
        membership.end_all(target_date=today)
        self.assertTrue(membership.active_subscriptions(target_date=tomorrow).count() == 0)

        # Check to make sure no bill will generate tomorrow
        ended_bill_batch = BillingBatch.objects.run(start_date=tomorrow, end_date=tomorrow)
        bill_after_end_date = user.bills.filter(period_start=tomorrow)
        self.assertTrue(len(bill_after_end_date) == 0)

    def test_room_booking_hours_user_less_than_allowance(self):
        # Create subscription for 10 room booking hours
        start = one_month_ago + timedelta(days=2)
        user = User.objects.create(username='member_twentyseven', first_name='Member', last_name='Twentyseven')
        membership = Membership.objects.for_user(user)
        membership.bill_day = start.day
        membership.set_to_package(self.eventPackage, start_date=start)
        self.assertEqual(1, membership.active_subscriptions().count())

        # Create event for 6 hours
        event1 = Event.objects.create(user=user, start_ts=localtime(now()) - timedelta(hours=6), end_ts=localtime(now()), room=Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00, members_only=False))

        # Make sure bill returns with line for subscription and one line for event
        new_bill_batch = BillingBatch.objects.run(start_date=start, end_date = (start + relativedelta(months=1) - timedelta(days=1)))
        self.assertTrue(new_bill_batch.successful)
        user_bill = user.bills.get(period_start=start, period_end=start + relativedelta(months=1) - timedelta(days=1))
        self.assertEqual(100, user_bill.amount)
        # Should have 2 line items. One for the subscription & one for the event
        self.assertEqual(2, user_bill.line_items.all().count())

    def test_room_booking_hour_overage(self):
        # Create subscription for 10 room booking hours
        start = one_month_ago + timedelta(days=2)
        user = User.objects.create(username='member_twentyeight', first_name='Member', last_name='Twentyeight')
        membership = Membership.objects.for_user(user)
        membership.bill_day = start.day
        membership.set_to_package(self.eventPackage, start_date=start)
        self.assertEqual(1, membership.active_subscriptions().count())

        # Create event for 12 hours
        event1 = Event.objects.create(user=user, start_ts=localtime(now()) - timedelta(hours=12), end_ts=localtime(now()), room=Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00, members_only=False))

        # Run billing batch
        new_bill_batch = BillingBatch.objects.run(start_date=start, end_date=(start + relativedelta(months=1) - timedelta(days=1)))
        self.assertTrue(new_bill_batch.successful)
        user_bill = user.bills.get(period_start=start, period_end=start + relativedelta(months=1) - timedelta(days=1))

        # Should have overage of $40 due to 2 extra room booking hours over allowance
        self.assertEqual(event1.bill, user_bill)
        self.assertEqual(140, user_bill.amount)
        # Should have 2 line items. One for the subscription & one for the event
        self.assertEqual(2, user_bill.line_items.all().count())

    # Not ready yet
    # def test_room_booking_for_inactive_member(self):
    #     user = User.objects.create(username='member_twentynine', first_name='Member', last_name='Twentynine')
    #
    #     event1 = Event.objects.create(user=user, start_ts=localtime(now()) - timedelta(hours=36), end_ts=localtime(now())-timedelta(hours=34), room=Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00, members_only=False))
    #
    #     new_bill_batch = BillingBatch.objects.run(start_date=one_month_ago, end_date=today)
    #     self.assertTrue(new_bill_batch.successful)
    #
    #     user_bill = user.bills.get(period_start=today, period_end=today)
    #     print_bill(user_bill)
    #     self.assertEqual(event1.bill, user_bill)
    #     self.assertEqual(40, user_bill.amount)
    #     # Should have 1 line items. Just one for the event
    #     self.assertEqual(1, user_bill.line_items.all().count())


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
