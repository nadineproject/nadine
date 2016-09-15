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
from nadine.models.core import *


def print_user_data(user):
    print
    profile = user.get_profile()
    print("Profile: %s" % profile)
    for bill in Bill.objects.filter(user=user):
        print("  Bill: %s" % bill)
        print("    Membership: %s" % bill.membership)
        for dropin in bill.dropins.all():
            print("    Drop-in: %s" % dropin)


class MembershipTestCase(TestCase):

    def setUp(self):
        self.residentPlan = MembershipPlan.objects.create(name="Resident", monthly_rate=475, dropin_allowance=5, daily_rate=20, has_desk=True)
        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        self.user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')

    def test_membership(self):
        orig_membership = Membership.objects.create(user=self.user1, member=self.user1.get_profile(), membership_plan=self.residentPlan, start_date=date(2008, 2, 10))
        self.assertTrue(orig_membership.is_anniversary_day(date(2010, 4, 10)))
        self.assertTrue(orig_membership.is_active())
        orig_membership.end_date = orig_membership.start_date + timedelta(days=31)
        orig_membership.save()
        self.assertFalse(orig_membership.is_active())
        new_membership = Membership(start_date=orig_membership.end_date, user=orig_membership.user, member=orig_membership.member, membership_plan=orig_membership.membership_plan)
        self.assertRaises(Exception, new_membership.save)  # the start date is the same as the previous plan's end date, which is an error
        new_membership.start_date = orig_membership.end_date + timedelta(days=1)
        new_membership.save()
        new_membership.end_date = new_membership.start_date + timedelta(days=64)
        new_membership.start_date = new_membership.end_date + timedelta(days=12)
        self.assertRaises(Exception, new_membership.save)  # the start date can't be the same or later than the end date

    def test_date_methods(self):
        test_date = date(2013, 3, 15)
        # Billing day was yesterday
        m1 = Membership.objects.create(user=self.user1, member=self.user1.get_profile(), membership_plan=self.residentPlan, start_date=date(2012, 6, 14))
        self.assertEquals(m1.prev_billing_date(test_date), date(2013, 3, 14))
        self.assertEquals(m1.next_billing_date(test_date), date(2013, 4, 14))
        # Billing day is today
        m2 = Membership.objects.create(user=self.user2, member=self.user2.get_profile(), membership_plan=self.residentPlan, start_date=date(2012, 6, 15))
        self.assertEquals(m2.prev_billing_date(test_date), date(2013, 3, 15))
        self.assertEquals(m2.next_billing_date(test_date), date(2013, 4, 15))
        # Billing day is tomorrow
        m3 = Membership.objects.create(user=self.user3, member=self.user3.get_profile(), membership_plan=self.residentPlan, start_date=date(2012, 6, 16))
        self.assertEquals(m3.prev_billing_date(test_date), date(2013, 2, 16))
        self.assertEquals(m3.next_billing_date(test_date), date(2013, 3, 16))
        # Make sure it works with the end of the months that have 28, 30, and 31 days
        m4 = Membership.objects.create(user=self.user4, member=self.user4.get_profile(), membership_plan=self.residentPlan, start_date=date(2012, 3, 31))
        self.assertEquals(m4.prev_billing_date(test_date), date(2013, 2, 28))
        # What about leap years?
        test_date = date(2012, 3, 15)
        m5 = Membership.objects.create(user=self.user5, member=self.user5.get_profile(), membership_plan=self.residentPlan, start_date=date(2011, 3, 31))
        self.assertEquals(m5.prev_billing_date(test_date), date(2012, 2, 29))


# Copyright 2015 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
