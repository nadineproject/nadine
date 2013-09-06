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
from staff.models import Bill, Transaction, Member, Membership, MembershipPlan, DailyLog, Onboard_Task, Onboard_Task_Completed, ExitTask, ExitTaskCompleted, Neighborhood

class MailingListTest(TestCase):
   
	def setUp(self):
		self.mlist1 = MailingList.objects.create(
			name='Hat Styles', description='All about les chapeau', subject_prefix='hat',
			email_address='hats@example.com', username='hat', password='1234',
			pop_host='localhost', smtp_host='localhost'
		)

		resident_plan = MembershipPlan(name="Resident",monthly_rate="475",dropin_allowance="5",daily_rate="20",deposit_amount="500",has_desk=True)

		self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
		Membership.objects.create(member=self.user1.get_profile(), membership_plan=resident_plan, start_date=date(2008, 6, 26))

		self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
		Membership.objects.create(member=self.user2.get_profile(), membership_plan=resident_plan, start_date=date(2008, 6, 26), end_date=(timezone.now().date() - timedelta(days=1)))

		self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
		Membership.objects.create(member=self.user3.get_profile(), membership_plan=resident_plan, start_date=date(2008, 6, 26), end_date=(timezone.now().date() - timedelta(days=1)))
		Membership.objects.create(member=self.user3.get_profile(), membership_plan=resident_plan, start_date=timezone.now().date())

	def test_auto_unsubscribe(self):
		self.mlist1.subscribers.add(self.user1)
		self.mlist1.subscribers.add(self.user2)
		self.mlist1.subscribers.add(self.user3)
		Member.objects.unsubscribe_recent_dropouts()
		self.assertTrue(self.user1 in self.mlist1.subscribers.all())
		self.assertFalse(self.user2 in self.mlist1.subscribers.all())
		self.assertTrue(self.user3 in self.mlist1.subscribers.all())

class UtilsTest(TestCase):
	
	def test_monthly_ranges(self):
		self.assertEqual(beginning_of_next_month(date(2010, 1, 1)), date(2010, 2, 1))
		self.assertEqual(beginning_of_next_month(date(2010, 6, 30)), date(2010, 7, 1))
		self.assertEqual(beginning_of_next_month(date(2010, 12, 1)), date(2011, 1, 1))
		self.assertEqual(first_days_in_months(date(2010, 1, 3), date(2010, 4, 4)), [date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1), date(2010, 4, 1)])
		self.assertEqual(first_days_in_months(date(2009, 12, 3), date(2010, 4, 4)), [date(2009, 12, 1), date(2010, 1, 1), date(2010, 2, 1), date(2010, 3, 1), date(2010, 4, 1)])
		self.assertEqual(first_days_in_months(date(2010, 1, 3), date(2010, 1, 3)), [date(2010, 1, 1)])
		self.assertEqual(first_days_in_months(date(2010, 1, 3), date(2010, 1, 14)), [date(2010, 1, 1)])
		self.assertEqual(first_days_in_months(date(2009, 12, 3), date(2010, 1, 14)), [date(2009, 12, 1), date(2010, 1, 1)])

class TasksTestCase(TestCase):

	def setUp(self):
		residentPlan = MembershipPlan(name="Resident",monthly_rate="475",dropin_allowance="5",daily_rate="20",deposit_amount="500")
		basicPlan = MembershipPlan(name="Basic",monthly_rate="25",dropin_allowance="1",daily_rate="20",deposit_amount="500")
		
		self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
		Membership.objects.create(member=self.user1.get_profile(), membership_plan=residentPlan, start_date=date(2008, 6, 26), has_desk=True)

		self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
		Membership.objects.create(member=self.user2.get_profile(), membership_plan=residentPlan, start_date=date(2008, 6, 26), end_date=(timezone.now().date() - timedelta(days=1)), has_desk=True)

		self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
		Membership.objects.create(member=self.user3.get_profile(), membership_plan=basicPlan, start_date=date(2008, 6, 26))

		self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
		Membership.objects.create(member=self.user4.get_profile(), membership_plan=basicPlan, start_date=date(2008, 6, 26), end_date=(timezone.now().date() - timedelta(days=1)))

		self.on_task_1 = Onboard_Task.objects.create(name="Give Desk", order=1, description="Give the member a desk.", has_desk_only=True)
		self.on_task_2 = Onboard_Task.objects.create(name="Entry Tat", order=2, description="Tattoo a bar code on the neck.", has_desk_only=False)

		self.exit_task_1 = ExitTask.objects.create(name="Exit Shaming", order=1, description="The parade of shame.", has_desk_only=False)
		self.exit_task_2 = ExitTask.objects.create(name="Clean Desk", order=2, description="Clean the member's old desk.", has_desk_only=True)


	def testTasks(self):
		self.assertEqual(Onboard_Task_Completed.objects.filter(member=self.user1.profile).count(), 0)
		self.assertEqual(ExitTaskCompleted.objects.filter(member=self.user1.profile).count(), 0)

		self.assertTrue(self.user1.profile.is_active())
		self.assertFalse(self.user2.profile.is_active())
		self.assertTrue(self.user3.profile.is_active())
		self.assertFalse(self.user4.profile.is_active())
		self.assertTrue(self.user1.profile.has_desk())
		self.assertFalse(self.user2.profile.has_desk())
		self.assertFalse(self.user3.profile.has_desk())
		self.assertFalse(self.user4.profile.has_desk())

		self.assertTrue(self.user1.profile in self.on_task_1.uncompleted_members())
		self.assertFalse(self.user2.profile in self.on_task_1.uncompleted_members()) # ended memberships don't require onboard tasks
		self.assertFalse(self.user3.profile in self.on_task_1.uncompleted_members()) # doesn't have a desk
		self.assertFalse(self.user4.profile in self.on_task_1.uncompleted_members()) # doesn't have a desk

		Onboard_Task_Completed.objects.create(member=self.user1.profile, task=self.on_task_1)
		self.assertFalse(self.user1.profile in self.on_task_1.uncompleted_members())

		self.assertFalse(self.user1.profile in self.exit_task_1.uncompleted_members())
		self.assertTrue(self.user2.profile in self.exit_task_1.uncompleted_members())

		ExitTaskCompleted.objects.create(member=self.user2.profile, task=self.exit_task_1)
		self.assertFalse(self.user2.profile in self.exit_task_1.uncompleted_members())

class MemberTestCase(TestCase):
	def setUp(self):
		self.neighborhood1 = Neighborhood.objects.create(name="Beggar's Gulch")
		self.basicPlan = MembershipPlan.objects.create(name="Basic",monthly_rate=50,dropin_allowance=3,daily_rate=20,deposit_amount=0,has_desk=False)
		self.pt5Plan = MembershipPlan.objects.create(name="PT5",monthly_rate=75,dropin_allowance=5,daily_rate=20,deposit_amount=0,has_desk=False)
		self.residentPlan = MembershipPlan.objects.create(name="Resident",monthly_rate=475,dropin_allowance=5,daily_rate=20,deposit_amount=500,has_desk=True)

		self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
		self.profile1 = self.user1.profile
		self.profile1.neighborhood=self.neighborhood1
		self.profile1.valid_billing = True
		self.profile1.save()
		Membership.objects.create(member=self.user1.get_profile(), membership_plan=self.basicPlan, start_date=date(2008, 2, 26), end_date=date(2010, 6, 25))
		Membership.objects.create(member=self.user1.get_profile(), membership_plan=self.residentPlan, start_date=date(2010, 6, 26))

		self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
		self.profile2 = self.user2.profile
		Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1))

		self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
		self.profile3 = self.user3.profile
		self.profile3.neighborhood=self.neighborhood1
		self.profile3.save()
		self.user3.profile.save()

		self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
		self.profile4 = self.user4.profile
		self.profile4.neighborhood=self.neighborhood1
		self.profile4.save()
		Membership.objects.create(member=self.user4.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), end_date=date(2010, 1, 1))
		
		self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
		self.profile5 = self.user5.profile
		self.profile5.valid_billing = False
		self.profile5.save()
		Membership.objects.create(member=self.user5.get_profile(), membership_plan=self.pt5Plan, start_date=date(2009, 1, 1), guest_of=self.profile1)
		
	def testInfoMethods(self):
		self.assertTrue(self.user1.profile in Member.objects.members_by_plan_id(self.residentPlan.id))
		self.assertFalse(self.user1.profile in Member.objects.members_by_plan_id(self.basicPlan.id))
		self.assertTrue(self.user2.profile in Member.objects.members_by_plan_id(self.pt5Plan.id))
		self.assertFalse(self.user2.profile in Member.objects.members_by_plan_id(self.residentPlan.id))

		self.assertTrue(self.user1.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
		self.assertFalse(self.user2.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
		self.assertFalse(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
		self.assertFalse(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
		self.assertTrue(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))
		self.assertTrue(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))
	
	def testValidBilling(self):
		# Member 1 has valid billing
		self.assertTrue(self.user1.profile.valid_billing)
		self.assertTrue(self.user1.profile.has_valid_billing())
		# Member 2 does not have valid billing
		self.assertFalse(self.user2.profile.valid_billing)
		self.assertFalse(self.user2.profile.has_valid_billing())
		# Member 5 does not have valid billing but is a guest of Member 1
		self.assertFalse(self.user5.profile.valid_billing)
		self.assertTrue(self.user5.profile.has_valid_billing())

class BillingTestCase(TestCase):

	def setUp(self):
		self.basicPlan = MembershipPlan.objects.create(name="Basic",monthly_rate=50,dropin_allowance=3,daily_rate=20,deposit_amount=0,has_desk=False)
		self.pt5Plan = MembershipPlan.objects.create(name="PT5",monthly_rate=75,dropin_allowance=5,daily_rate=20,deposit_amount=0,has_desk=False)
		self.pt15Plan = MembershipPlan.objects.create(name="PT15",monthly_rate=225,dropin_allowance=15,daily_rate=20,deposit_amount=0,has_desk=False)
		self.residentPlan = MembershipPlan.objects.create(name="Resident",monthly_rate=475,dropin_allowance=5,daily_rate=20,deposit_amount=500,has_desk=True)

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

	def testMembership(self):
		orig_membership = Membership.objects.create(member=self.user1.get_profile(), membership_plan=self.residentPlan, start_date=date(2008, 2, 10))
		self.assertTrue(orig_membership.is_anniversary_day(date(2010, 4, 10)))
		self.assertTrue(orig_membership.is_active())
		orig_membership.end_date = orig_membership.start_date + timedelta(days=31)
		orig_membership.save()
		self.assertFalse(orig_membership.is_active())
		new_membership = Membership(start_date=orig_membership.end_date, member=orig_membership.member, membership_plan=orig_membership.membership_plan)
		self.assertRaises(Exception, new_membership.save) # the start date is the same as the previous plan's end date, which is an error
		new_membership.start_date = orig_membership.end_date + timedelta(days=1)
		new_membership.save()
		new_membership.end_date = new_membership.start_date + timedelta(days=64)
		new_membership.start_date = new_membership.end_date + timedelta(days=12)
		self.assertRaises(Exception, new_membership.save) # the start date can't be the same or later than the end date

	def testTags (self):
		member1 = self.user1.get_profile()
		member1.tags.add("coworking", "books", "beer")
		member2 = self.user2.get_profile()
		member2.tags.add("beer", "cars", "women")
		member3 = self.user3.get_profile()
		member3.tags.add("knitting", "beer", "travel")
		self.assertTrue(member1 in Member.objects.filter(tags__name__in=["beer"]))
		self.assertTrue(member2 in Member.objects.filter(tags__name__in=["beer"]))
		self.assertTrue(member3 in Member.objects.filter(tags__name__in=["beer"]))
		self.assertFalse(member1 in Member.objects.filter(tags__name__in=["knitting"]))
		self.assertFalse(member3 in Member.objects.filter(tags__name__in=["books"]))

	def testRun(self):
		member1 = self.user1.get_profile()
		member2 = self.user2.get_profile()
		member3 = self.user3.get_profile()
		member4 = self.user4.get_profile()
		member5 = self.user5.get_profile()

		end_time = datetime(2010, 6, 30)
		day_range = range(30)
		day_range.reverse()
		days = [end_time - timedelta(days=i) for i in day_range]
		# 2010-06-1 through 2010-06-30
		for day in days:
			#print 'Testing: %s' % (day)
			billing.run_billing(day)
			if day.day == 1:
				# User5's PT15 membership
				self.assertTrue(member5.last_bill() != None)
				self.assertEqual(member5.last_bill().membership, Membership.objects.get(member=member5, membership_plan=self.pt15Plan.id))
				self.assertEquals(member5.last_bill().amount, self.pt15Plan.monthly_rate)
				self.assertEquals(member5.last_bill().amount, self.pt15Plan.monthly_rate)
			if day.day == 10:
				# User4's PT5 membership
				self.assertTrue(member4.last_bill() != None)
				self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
				self.assertEqual(member4.last_bill().membership, Membership.objects.get(member=member4, membership_plan=self.pt5Plan.id))
				self.assertEqual(member4.last_bill().dropins.count(), 9) # dropins on 6/2 - 6/10
				self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - self.pt5Plan.dropin_allowance) * self.pt5Plan.daily_rate)
			if day.day == 11:
				self.assertTrue(member4.last_bill() != None)
				self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
				self.assertEqual(member4.last_bill().membership, Membership.objects.get(member=member4, membership_plan=self.residentPlan.id))
				self.assertEqual(member4.last_bill().dropins.count(), 0)
			if day.day == 16:
				# User 5's PT15
				# Should be 15 dropins but they were part of the PT15 plan so no extra charges should be on this bill
				self.assertTrue(member5.last_bill() != None)
				self.assertTrue(member5.last_bill().created.month == day.month and member5.last_bill().created.day == day.day)
				self.assertEqual(member5.last_bill().membership, Membership.objects.get(member=member5, membership_plan=self.pt15Plan.id))
				self.assertEqual(member5.last_bill().dropins.count(), 15)
				self.assertEquals(member5.last_bill().amount, 0)
			if day.day == 17:
				# User 5's Basic membership
				self.assertTrue(member5.last_bill() != None)
				self.assertEqual(member5.last_bill().membership, Membership.objects.get(member=member5, membership_plan=self.basicPlan.id))
				self.assertEqual(member5.last_bill().dropins.count(), 0)
				self.assertEquals(member5.last_bill().amount, self.basicPlan.monthly_rate)
			if day.day == 20:
				self.assertTrue(member3.last_bill() != None)
				self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
				self.assertEqual(member3.last_bill().dropins.count(), 17)
			if day.day == 21:
				self.assertTrue(member3.last_bill() != None)
				self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
				self.assertEqual(member3.last_bill().dropins.count(), 0)
			if day.day == 26:
				self.assertTrue(member1.last_membership().is_anniversary_day(day))
				member_bills = member1.bills.all().order_by('-created')
				self.assertTrue(len(member_bills) > 0)
				self.assertTrue(member_bills[0].membership == member1.last_membership())
			if day.day == 30:
				self.assertTrue(member2.last_membership().is_anniversary_day(day))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
