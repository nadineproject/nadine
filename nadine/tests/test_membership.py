import traceback
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.urls import reverse

from django.test import TestCase, RequestFactory, Client
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.contrib.auth.models import User

from nadine.models.membership import *
from nadine.models.resource import Resource
from nadine.models.organization import Organization

today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)

class MembershipTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.org3 = Organization.objects.create(lead=self.user3, name="User3 Org", created_by=self.user3)

        # Resources
        self.test_resource = Resource.objects.create(name="Test Resource")

        # Membership package
        self.test_package = MembershipPackage.objects.create(name="Test Package")
        self.default_subscription = SubscriptionDefault.objects.create(
            package = self.test_package,
            resource = self.test_resource,
            allowance = 10,
            monthly_rate = 100,
            overage_rate = 20,
        )

        # Starts today and no end
        self.membership1 = self.create_membership(
            start = today,
            monthly_rate = 100,
        )

        # Starts today and ends in a month
        self.membership2 = self.create_membership(
            start = today,
            end = one_month_from_now,
            monthly_rate = 200.00,
        )

        # Starts in a month
        self.membership3 = self.create_membership(
            start = one_month_from_now,
            monthly_rate = 300.00,
        )

        # Started a month ago and ends today
        self.membership4 = self.create_membership(
            start = one_month_ago,
            end = today,
            monthly_rate = 400.00,
        )

        # Ended yesterday
        self.membership5 = self.create_membership(
            start = one_month_ago,
            end = yesterday,
            monthly_rate = 500.00,
        )

        # All last year
        self.membership6 = self.create_membership(
            start = date(year=today.year-1, month=1, day=1),
            end = date(year=today.year-1, month=12, day=31),
            monthly_rate = 600.00,
        )

        # Start and end on the same day of the month, last year for 8 months
        self.membership7 = self.create_membership(
            start = date(year=today.year-1, month=2, day=1),
            end =  date(year=today.year-1, month=10, day=1),
            monthly_rate = 700.00,
        )

        # Pro rated end
        self.membership8 = self.create_membership(
            start = date(year=today.year-1, month=2, day=1),
            end =  date(year=today.year-1, month=10, day=18),
            monthly_rate = 800.00,
        )

        # One period in the past
        self.membership9 = self.create_membership(
            start = date(year=today.year-1, month=2, day=1),
            end =  date(year=today.year-1, month=3, day=1),
            monthly_rate = 900.00,
        )

        # One period in the future
        self.membership10 = self.create_membership(
            start = date(year=today.year+1, month=3, day=1),
            end =  date(year=today.year+1, month=3, day=31),
            monthly_rate = 1000.00,
        )

    ############################################################################
    # Helper Methods
    ############################################################################

    def create_membership(self, bill_day=0, start=None, end=None, resource=None, monthly_rate=100, overage_rate=20):
        if not start:
            start = today
        if bill_day == 0:
            bill_day = start.day
        if not resource:
            resource = self.test_resource
        membership = Membership.objects.create(bill_day=bill_day)
        ResourceSubscription.objects.create(
            membership = membership,
            resource = resource,
            start_date = start,
            end_date = end,
            monthly_rate = monthly_rate,
            overage_rate = overage_rate,
        )
        return membership

    def period_boundary_test(self, period_start, period_end):
        # For a given period start, test the period_end is equal to the given period_end
        m = self.create_membership(start=period_start)
        ps, pe = m.get_period(target_date=period_start)
        # print("start: %s, end: %s, got: %s" % (period_start, period_end, pe))
        self.assertEquals(pe, period_end)

    def next_period_start_test(self, start, number):
        last_start = start
        m = self.create_membership(start=start)
        # print("Created Membership: start_date = %s, bill_day = %s" % (start, m.bill_day))
        for i in range(0, number):
            test_date = start + relativedelta(months=i) + timedelta(days=1)
            # print("  Test(%d): %s" % (i, test_date))
            this_start, this_end = m.get_period(test_date)
            next_start = m.next_period_start(last_start)
            # print("   This period: %s to %s, Next: %s" % (this_start, this_end, next_start))
            self.assertEqual(next_start, this_end + timedelta(days=1))
            self.assertEqual(last_start, this_start)
            last_start = next_start

    ############################################################################
    # Tests
    ############################################################################

    def test_user_list(self):
        user1 = User.objects.create(username='user_one', first_name='User', last_name='One')
        user2 = User.objects.create(username='user_two', first_name='User', last_name='Two')
        user3 = User.objects.create(username='user_three', first_name='User', last_name='Three')

        # An individual membership should have only the individual
        user_list = user3.membership.user_list()
        self.assertEqual(1, len(user_list))
        self.assertEqual(user3, user_list[0])

        # An organization membership should have all members of that org
        org1 = Organization.objects.create(lead=user1, name="Test Org", created_by=user1)
        org1.add_member(user1)
        org1.add_member(user2)
        user_list = org1.membership.user_list()
        self.assertEqual(2, len(user_list))
        self.assertTrue(user1 in user_list)
        self.assertTrue(user2 in user_list)
        self.assertFalse(user3 in user_list)

    def test_start_date(self):
        # Our start date should be equal to the start of the first subscription
        membership = Membership.objects.create(bill_day=1)
        self.assertEqual(None, membership.start_date)
        ResourceSubscription.objects.create(
            membership = membership,
            resource = self.test_resource,
            start_date = date(2016,1,1),
            end_date = date(2016,5,31),
            monthly_rate = 100,
            overage_rate = 20,
        )
        self.assertEqual(date(2016,1,1), membership.start_date)
        # Create another subscription and test the start date does not change
        ResourceSubscription.objects.create(
            membership = membership,
            resource = self.test_resource,
            start_date = date(2016,6,1),
            monthly_rate = 200,
            overage_rate = 20,
        )
        self.assertEqual(date(2016,1,1), membership.start_date)

    def test_inactive_period(self):
        self.assertEquals((None, None), self.membership1.get_period(target_date=yesterday))
        self.assertEquals((None, None), self.membership2.get_period(target_date=yesterday))
        self.assertEquals((None, None), self.membership3.get_period(target_date=today))
        self.assertEquals((None, None), self.membership4.get_period(target_date=tomorrow))
        self.assertEquals((None, None), self.membership5.get_period(target_date=tomorrow))

    def test_get_period(self):
        # Test month bounderies
        self.period_boundary_test(date(2015, 1, 1), date(2015, 1, 31))
        self.period_boundary_test(date(2015, 2, 1), date(2015, 2, 28))
        self.period_boundary_test(date(2015, 3, 1), date(2015, 3, 31))
        self.period_boundary_test(date(2015, 4, 1), date(2015, 4, 30))
        self.period_boundary_test(date(2015, 5, 1), date(2015, 5, 31))
        self.period_boundary_test(date(2015, 6, 1), date(2015, 6, 30))
        self.period_boundary_test(date(2015, 7, 1), date(2015, 7, 31))
        self.period_boundary_test(date(2015, 8, 1), date(2015, 8, 31))
        self.period_boundary_test(date(2015, 9, 1), date(2015, 9, 30))
        self.period_boundary_test(date(2015, 10, 1), date(2015, 10, 31))
        self.period_boundary_test(date(2015, 11, 1), date(2015, 11, 30))
        self.period_boundary_test(date(2015, 12, 1), date(2015, 12, 31))

    def test_get_period_leap(self):
        # Leap year!
        self.period_boundary_test(date(2016, 2, 1), date(2016, 2, 29))
        self.period_boundary_test(date(2016, 3, 1), date(2016, 3, 31))

    def test_get_period_days(self):
        # Test Day bounderies
        for i in range(2, 31):
            self.period_boundary_test(date(2015, 7, i), date(2015, 8, i-1))

    def test_get_period_31st(self):
        # Test when the next following month has fewer days
        self.period_boundary_test(date(2015, 1, 29), date(2015, 2, 28))
        self.period_boundary_test(date(2015, 1, 30), date(2015, 2, 28))
        self.period_boundary_test(date(2015, 1, 31), date(2015, 2, 28))
        self.period_boundary_test(date(2016, 3, 31), date(2016, 4, 30))
        self.period_boundary_test(date(2017, 5, 31), date(2017, 6, 30))

    def test_get_period_bug(self):
        # Found this bug when I was testing so I created a special test for it --JLS
        m = self.create_membership(start=date(2017, 1, 28))
        ps, pe = m.get_period(date(2017, 3, 1))
        self.assertEqual(ps, date(2017, 2, 28))
        self.assertEqual(pe, date(2017, 3, 27))

    def test_get_period_bug2(self):
        # Another bug I found when testing --JLS
        # Membership = 1/31/17, Bill Day = 31st
        m = self.create_membership(start=date(2017, 1, 31))
        #  First Period: 1/31/17 - 2/28/17
        #  Next Period: 3/1/17 - 3/30/17
        ps, pe = m.get_period(date(2017, 3, 2))
        self.assertEqual(ps, date(2017, 3, 1))
        self.assertEqual(pe, date(2017, 3, 30))
        #  Period: 3/31/17 - 4/30/17
        ps, pe = m.get_period(date(2017, 4, 2))
        self.assertEqual(ps, date(2017, 3, 31))
        self.assertEqual(pe, date(2017, 4, 30))
        #  Period: 5/1/17 - 5/30/17
        ps, pe = m.get_period(date(2017, 5, 2))
        self.assertEqual(ps, date(2017, 5, 1))
        self.assertEqual(pe, date(2017, 5, 30))
        #  Period: 5/31/17 - 6/30/17
        ps, pe = m.get_period(date(2017, 6, 2))
        self.assertEqual(ps, date(2017, 5, 31))
        self.assertEqual(pe, date(2017, 6, 30))
        #  Period: 7/1/17 - 7/30/17
        ps, pe = m.get_period(date(2017, 7, 2))
        self.assertEqual(ps, date(2017, 7, 1))
        self.assertEqual(pe, date(2017, 7, 30))
        #  Period: 7/31/17 - 8/30/17
        ps, pe = m.get_period(date(2017, 8, 2))
        self.assertEqual(ps, date(2017, 7, 31))
        self.assertEqual(pe, date(2017, 8, 30))

    def test_is_period_boundary(self):
        m = self.create_membership(start=date(2016,1,1), end=date(2016,5,31))
        self.assertFalse(m.is_period_boundary(target_date=date(2016, 2, 15)))
        self.assertTrue(m.is_period_boundary(target_date=date(2016, 2, 29)))
        self.assertFalse(m.is_period_boundary(target_date=date(2016, 3, 15)))
        self.assertTrue(m.is_period_boundary(target_date=date(2016, 3, 31)))
        self.assertFalse(m.is_period_boundary(target_date=date(2016, 4, 15)))
        self.assertTrue(m.is_period_boundary(target_date=date(2016, 4, 30)))

    def test_next_period_start_active(self):
        self.assertEqual(self.membership1.next_period_start(), one_month_from_now)
        self.assertEqual(self.membership2.next_period_start(), one_month_from_now)

    def test_next_period_start_inactive(self):
        self.assertEqual(self.membership4.next_period_start(), None)
        self.assertEqual(self.membership5.next_period_start(), None)
        self.assertEqual(self.membership6.next_period_start(), None)
        self.assertEqual(self.membership7.next_period_start(), None)
        self.assertEqual(self.membership8.next_period_start(), None)
        self.assertEqual(self.membership9.next_period_start(), None)

    def test_next_period_start_future(self):
        self.assertEqual(self.membership3.next_period_start(), one_month_from_now)
        next_start = self.membership10.next_period_start()
        self.assertEqual(next_start.month, 3)
        self.assertEqual(next_start.day, 1)

    def test_next_period_start(self):
        # Start a membership on each day of the month and make sure the next
        # five years have valid period ranges and the right next_period_start
        # for i in range(1, 31):
            # self.next_period_start_test(date(2016, 1, i), 60)
        self.next_period_start_test(date(2016,1,1), 60)
        self.next_period_start_test(date(2016,1,10), 60)
        self.next_period_start_test(date(2017,1,28), 60)
        self.next_period_start_test(date(2016,1,31), 60)

    def test_active_memberships(self):
        active_memberships = Membership.objects.active_memberships()
        self.assertTrue(self.membership1 in active_memberships)
        self.assertTrue(self.membership2 in active_memberships)
        self.assertFalse(self.membership3 in active_memberships)
        self.assertTrue(self.membership4 in active_memberships)
        self.assertFalse(self.membership5 in active_memberships)
        self.assertFalse(self.membership6 in active_memberships)

    def test_is_active(self):
        self.assertTrue(self.membership1.is_active())
        self.assertTrue(self.membership2.is_active())
        self.assertFalse(self.membership3.is_active())
        self.assertTrue(self.membership4.is_active())
        self.assertFalse(self.membership5.is_active())
        self.assertFalse(self.membership6.is_active())
        self.assertFalse(self.membership7.is_active())

    def test_in_future(self):
        self.assertFalse(self.membership1.in_future())
        self.assertFalse(self.membership2.in_future())
        self.assertTrue(self.membership3.in_future())
        self.assertFalse(self.membership4.in_future())
        self.assertFalse(self.membership5.in_future())
        self.assertFalse(self.membership6.in_future())
        self.assertTrue(self.membership10.in_future())

    def test_prorated(self):
        r = self.membership8.subscriptions.first()
        # The first month was a full period so no prorate
        ps, pe = self.membership8.get_period(r.start_date)
        self.assertEqual(1, r.prorate_for_period(ps, pe))
        # The last month was partial so it was prorated
        ps, pe = self.membership8.get_period(r.end_date)
        self.assertTrue(1 > r.prorate_for_period(ps, pe))

    def test_bill_day_str(self):
        membership = self.user1.membership
        membership.bill_day = 1
        self.assertEquals("1st", membership.bill_day_str)
        membership.bill_day = 2
        self.assertEquals("2nd", membership.bill_day_str)
        membership.bill_day = 3
        self.assertEquals("3rd", membership.bill_day_str)
        membership.bill_day = 5
        self.assertEquals("5th", membership.bill_day_str)
        membership.bill_day = 11
        self.assertEquals("11th", membership.bill_day_str)
        membership.bill_day = 21
        self.assertEquals("21st", membership.bill_day_str)
        membership.bill_day = 22
        self.assertEquals("22nd", membership.bill_day_str)
        membership.bill_day = 23
        self.assertEquals("23rd", membership.bill_day_str)
        membership.bill_day = 25
        self.assertEquals("25th", membership.bill_day_str)
        membership.bill_day = 30
        self.assertEquals("30th", membership.bill_day_str)
        membership.bill_day = 31
        self.assertEquals("31st", membership.bill_day_str)

    def test_generate_bill(self):
        user1 = User.objects.create(username='user_gen1', first_name='Gen', last_name='One')
        user2 = User.objects.create(username='user_gen2', first_name='Gen', last_name='Two')
        membership = user1.membership
        subscription = ResourceSubscription.objects.create(
            membership = membership,
            resource = self.test_resource,
            start_date = two_months_ago,
            monthly_rate = 100.00,
            overage_rate = 0,
        )

        # Assume that if we generate a bill we will have a bill
        self.assertEquals(0, membership.bills.count())
        membership.generate_bill(target_date=today)
        self.assertEquals(1, membership.bills.count())

        # Check all the bill values
        bill = membership.bills.first()
        self.assertEquals(user1, bill.user)
        self.assertEquals(membership.monthly_rate(), bill.amount)
        ps, pe = membership.get_period(target_date=today)
        self.assertEquals(ps, bill.period_start)
        self.assertEquals(pe, bill.period_end)

        # Run it again and test it doesn't create another bill
        membership.generate_bill(target_date=today)
        self.assertEquals(1, membership.bills.count())
        self.assertEquals(membership.monthly_rate(), bill.amount)

    def test_generate_all_bills(self):
        user1 = User.objects.create(username='user_one', first_name='User', last_name='One')
        membership = user1.membership
        subscription = ResourceSubscription.objects.create(
            membership = membership,
            resource = self.test_resource,
            start_date = date(year=2016, month=1, day=1),
            end_date = date(year=2016, month=12, day=31),
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        self.assertEquals(0, membership.bills.count())
        membership.generate_all_bills()
        self.assertEquals(12, membership.bills.count())

    def test_package_monthly_rate(self):
        # Only 1 subscription so the totals should match
        self.assertEqual(self.test_package.monthly_rate(), self.default_subscription.monthly_rate)

    def test_set_to_package(self):
        user = User.objects.create(username='test_user1', first_name='Test', last_name='User')
        membership = user.membership

        # If this ended yesterday, the rate should be $0 today
        membership.end_all(yesterday)
        self.assertFalse(membership.matches_package())
        self.assertEqual(0, membership.monthly_rate())

        # Set this membership to our Test Package
        membership.set_to_package(self.test_package, today)
        self.assertEqual(membership.package, self.test_package)
        self.assertEqual(membership.monthly_rate(), self.test_package.monthly_rate())
        self.assertTrue(membership.matches_package())

        # Add a new subscription and the package should still be the same
        # but matches_package will no longer be true
        ResourceSubscription.objects.create(
            membership = membership,
            resource = self.test_resource,
            start_date = today,
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        self.assertFalse(membership.matches_package())
        self.assertEqual(membership.package, self.test_package)
        self.assertTrue(membership.monthly_rate(), self.test_package.monthly_rate() + 100)

    def test_subscription_payer(self):
        # Start with an OrganizationMembership
        org_membership = self.org3.membership
        subscription = ResourceSubscription.objects.create(
            membership = org_membership,
            resource = self.test_resource,
            start_date = today,
            monthly_rate = 100.00,
            overage_rate = 0,
        )
        self.assertEqual(self.user3, subscription.payer)

        # Now test an IndividualMembership
        subscription.membership = self.user2.membership
        self.assertEqual(self.user2, subscription.payer)

        # And finally mark this as paid_by someone else
        subscription.paid_by = self.user1
        self.assertEqual(self.user1, subscription.payer)

    def test_is_individual(self):
        i = self.user1.membership
        self.assertTrue(i.is_individual)
        self.assertFalse(i.is_organization)
        m = Membership.objects.get(id=i.id)
        self.assertTrue(m.is_individual)
        self.assertFalse(m.is_organization)

    def test_is_organization(self):
        o = self.org3.membership
        self.assertFalse(o.is_individual)
        self.assertTrue(o.is_organization)
        m = Membership.objects.get(id=o.id)
        self.assertFalse(m.is_individual)
        self.assertTrue(m.is_organization)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
