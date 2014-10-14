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

class MailingListTest(TestCase):
	def setUp(self):
		self.mlist1 = MailingList.objects.create(
			name='Hat Styles', description='All about les chapeau', subject_prefix='hat',
			email_address='hats@example.com', username='hat', password='1234',
			pop_host='localhost', smtp_host='localhost'
		)

		resident_plan = MembershipPlan(name="Resident",monthly_rate="475",dropin_allowance="5",daily_rate="20",has_desk=True)

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
		residentPlan = MembershipPlan(name="Resident",monthly_rate="475",dropin_allowance="5",daily_rate="20")
		basicPlan = MembershipPlan(name="Basic",monthly_rate="25",dropin_allowance="1",daily_rate="20")
		
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

	def test_tasks(self):
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

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
