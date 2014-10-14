import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import staff.billing as billing
from interlink.models import MailingList
from staff.views import beginning_of_next_month, first_days_in_months
from staff.models import *

def print_user_data(user):
	print
	profile = user.get_profile()
	print "Profile: %s" % profile
	for bill in Bill.objects.filter(member=profile):
		print "  Bill: %s" % bill
		print "    Membership: %s" % bill.membership
		for dropin in bill.dropins.all():
			print "    Drop-in: %s" % dropin

class BillingTestCase(TestCase):
	def setUp(self):
		self.basicPlan = MembershipPlan.objects.create(name="Basic",monthly_rate=50,dropin_allowance=3,daily_rate=20,has_desk=False)
		self.pt5Plan = MembershipPlan.objects.create(name="PT5",monthly_rate=75,dropin_allowance=5,daily_rate=20,has_desk=False)
		self.pt15Plan = MembershipPlan.objects.create(name="PT15",monthly_rate=225,dropin_allowance=15,daily_rate=20,has_desk=False)
		self.residentPlan = MembershipPlan.objects.create(name="Resident",monthly_rate=475,dropin_allowance=5,daily_rate=20,has_desk=True)

		# User 1 = Resident since 6/26/2008 
		self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
		Membership.objects.create_with_plan(member=self.user1.get_profile(), start_date=date(2008, 6, 26), end_date=None, membership_plan=self.residentPlan)

		# User 2 = Resident since 1/31/2008 
		self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
		Membership.objects.create_with_plan(member=self.user2.get_profile(), start_date=date(2008, 1, 31), end_date=None, membership_plan=self.residentPlan)

		# User 3 = PT15 2/1/2008 - 6/20/2010 & Basic since 6/21/2010
		# Daily activity 6/2/2010 through 6/19/2010
		self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
		Membership.objects.create_with_plan(member=self.user3.get_profile(), start_date=date(2008, 2, 1), end_date=date(2010, 6, 20), membership_plan=self.pt15Plan)
		Membership.objects.create_with_plan(member=self.user3.get_profile(), start_date=date(2010, 6, 21), end_date=None, membership_plan=self.basicPlan)
		for day in range(2,19): DailyLog.objects.create(member=self.user3.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

		# User 4 = PT5 2/1/2008 - 6/10/2010 & Resident since 6/11/2010
		# Daily activity 6/2/2010 through 6/11/2010
		self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')		  
		Membership.objects.create_with_plan(member=self.user4.get_profile(), start_date=date(2008, 2, 1), end_date=date(2010, 6, 10), membership_plan=self.pt5Plan)
		Membership.objects.create_with_plan(member=self.user4.get_profile(), start_date=date(2010, 6, 11), end_date=None, membership_plan=self.residentPlan)
		for day in range(2,11): DailyLog.objects.create(member=self.user4.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

		# User 5 = PT15 5/20/2010 - 6/16/2010 & Basic since 6/17/2010
		# Daily activity 6/1/2010 through 6/15/2010
		self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')		  
		Membership.objects.create_with_plan(member=self.user5.get_profile(), start_date=date(2010, 5, 20), end_date=date(2010, 6, 16), membership_plan=self.pt15Plan)
		Membership.objects.create_with_plan(member=self.user5.get_profile(), start_date=date(2010, 6, 17), end_date=None, membership_plan=self.basicPlan)
		for day in range(1,16): DailyLog.objects.create(member=self.user5.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

		# User 6, 7 = PT-5 6/26/2008 - User 7 guest of User 6
		# User 7 has daily activity 6/1/2010 through 6/15/2010
		self.user6 = User.objects.create(username='member_six', first_name='Member', last_name='Six')
		self.user7 = User.objects.create(username='member_seven', first_name='Member', last_name='Seven')
		Membership.objects.create_with_plan(member=self.user6.get_profile(), start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan)
		Membership.objects.create_with_plan(member=self.user7.get_profile(), start_date=date(2008, 6, 26), end_date=None, membership_plan=self.pt5Plan, rate=0, guest_of=self.user6.get_profile())
		for day in range(1,16): DailyLog.objects.create(member=self.user7.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

		# User 8 = PT-5 5/20/2010 - 6/19/2010 & Basic since 6/20/2010
		# Daily activity 6/11/2010 through 6/23/2010
		self.user8 = User.objects.create(username='member_eight', first_name='Member', last_name='Eight')		  
		Membership.objects.create_with_plan(member=self.user8.get_profile(), start_date=date(2010, 5, 20), end_date=date(2010, 6, 19), membership_plan=self.pt5Plan)
		Membership.objects.create_with_plan(member=self.user8.get_profile(), start_date=date(2010, 6, 20), end_date=None, membership_plan=self.basicPlan)
		for day in range(11,23): DailyLog.objects.create(member=self.user8.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

	def test_guest_activity(self):
		test_date = date(2010, 6, 20)
		member6 = self.user6.get_profile()
		member7 = self.user7.get_profile()
		self.assertEqual(member7.is_guest(), member6)
		self.assertTrue(member7 in member6.guests())
		self.assertEqual(len(member6.activity_this_month(test_date)), 15)

	def test_run(self):
		member1 = self.user1.get_profile()
		member2 = self.user2.get_profile()
		member3 = self.user3.get_profile()
		member4 = self.user4.get_profile()
		member5 = self.user5.get_profile()
		member6 = self.user6.get_profile()
		member7 = self.user7.get_profile()
		member8 = self.user8.get_profile()

		end_time = datetime(2010, 6, 30)
		day_range = range(30)
		day_range.reverse()
		days = [end_time - timedelta(days=i) for i in day_range]
		# 2010-06-1 through 2010-06-30
		for day in days:
			#print 'Testing: %s' % (day)
			billing.run_billing(day)
			if day.day == 10:
				# User4's PT5 membership
				self.assertTrue(member4.last_bill() != None, "Member4 should have had a bill")
				self.assertEqual(member4.last_bill().membership.membership_plan, self.pt5Plan)
				self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
				self.assertEqual(member4.last_bill().membership, Membership.objects.get(member=member4, membership_plan=self.pt5Plan.id))
				self.assertEqual(member4.last_bill().dropins.count(), 9) # dropins on 6/2 - 6/10
				self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - self.pt5Plan.dropin_allowance) * self.pt5Plan.daily_rate)
			if day.day == 11:
				# User4's Resident membership
				self.assertTrue(member4.last_bill() != None)
				self.assertEqual(member4.last_bill().membership.membership_plan, self.residentPlan)
				self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
				self.assertEqual(member4.last_bill().dropins.count(), 0)
			if day.day == 16:
				# User 5's PT15
				# Should be 15 dropins but they were part of the PT15 plan so no extra charges should be on this bill
				self.assertTrue(member5.last_bill() != None)
				self.assertEqual(member5.last_bill().membership.membership_plan, self.pt15Plan)
				self.assertTrue(member5.last_bill().created.month == day.month and member5.last_bill().created.day == day.day)
				self.assertEqual(member5.last_bill().membership, Membership.objects.get(member=member5, membership_plan=self.pt15Plan.id))
				#TODOself.assertEqual(member5.last_bill().dropins.count(), 15)
				self.assertEquals(member5.last_bill().amount, 0)
			if day.day == 17:
				# User 5's Basic membership
				self.assertTrue(member5.last_bill() != None)
				self.assertEqual(member5.last_bill().membership, Membership.objects.get(member=member5, membership_plan=self.basicPlan.id))
				self.assertEqual(member5.last_bill().dropins.count(), 0)
				self.assertEquals(member5.last_bill().amount, self.basicPlan.monthly_rate)
			if day.day == 19:
				# User 8's PT-5 membership (9 days)
				self.assertTrue(member8.last_bill() != None)
				self.assertEqual(member8.last_bill().membership.membership_plan, self.pt5Plan)
				self.assertEqual(member8.last_bill().dropins.count(), 9)
				self.assertEquals(member8.last_bill().amount, 80)
				True
			if day.day == 20:
				# User 3's PT-15 membership
				self.assertTrue(member3.last_bill() != None)
				self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
				self.assertEqual(member3.last_bill().dropins.count(), 17)
				
				# User 8's Basic membership (1 days)
				self.assertTrue(member8.last_bill() != None)
				self.assertEqual(member8.last_bill().membership.membership_plan, self.basicPlan)
				self.assertEqual(member8.last_bill().dropins.count(), 1)
			if day.day == 21:
				self.assertTrue(member3.last_bill() != None)
				self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
				self.assertEqual(member3.last_bill().dropins.count(), 0)
			if day.day == 26:
				# User 1
				self.assertTrue(member1.last_membership().is_anniversary_day(day))
				member_bills = member1.bills.all().order_by('-created')
				self.assertTrue(len(member_bills) > 0)
				self.assertTrue(member_bills[0].membership == member1.last_membership())
				
				# User 6's PT-5, User 7's PT-5
				# User 7 guest of user 6 and used 15 days
				self.assertEqual(member7.is_guest(), member6)
				self.assertTrue(member7.last_bill() != None)
				self.assertEqual(member7.last_bill().dropins.count(), 0)
				self.assertEquals(member7.last_bill().amount, 0)
				self.assertTrue(member6.last_bill() != None)
				self.assertEqual(member6.last_bill().dropins.count(), 0)
				self.assertEqual(member6.last_bill().guest_dropins.count(), 15)
				# $75 base rate + 10 overage days @ $20 = $275
				self.assertEquals(member6.last_bill().amount, 275)
			if day.day == 30:
				self.assertTrue(member2.last_membership().is_anniversary_day(day))

		# print_user_data(self.user1)
		# print_user_data(self.user2)
		# print_user_data(self.user3)
		# print_user_data(self.user4)
		# print_user_data(self.user5)
		# print_user_data(self.user6)
		# print_user_data(self.user7)
		# print_user_data(self.user8)
		
	def test_drop_in_on_billing_date_is_associated_with_correct_bill(self):
		member8 = self.user8.get_profile()
		print_user_data(self.user8)
		
		end_time = datetime(2010, 7, 31)
		day_range = range(61)
		day_range.reverse()
		days = [end_time - timedelta(days=i) for i in day_range]
		for day in days:
			billing.run_billing(day)

		bills = Bill.objects.filter(member=member8).order_by("created")
		print bills
		# self.assertEqual(bills.count(), 5, "Member8 had the incorrect number of bills (%d)" % bills.count())
		may_20_pt5 = bills[0]
		may_20_overage = bills[1]
		june_20_basic = bills[2]
		june_20_overage = bills[3]
		#july_20_basic = bills[4]

		self.assertTrue(may_20_pt5 != None)
		self.assertEqual(date(2010, 5, 20), may_20_pt5.created)
		
		# 		self.assertEqual(pre_june_20.membership.membership_plan, self.pt5Plan)
		# 		self.assertEqual(pre_june_20.dropins.count(), 9, "Member8 had wrong number of dropin days")
		# 		self.assertEquals(pre_june_20.amount, 80)

		# User 8's Basic membership (1 days)
		# self.assertTrue(june_20_july_19 != None)
		# 		self.assertEqual(june_20_july_19.membership.membership_plan, self.basicPlan)
		# 		self.assertEqual(june_20_july_19.dropins.count(), 1)
		

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
