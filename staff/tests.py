from datetime import datetime, timedelta, date
import traceback

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User

import settings
from staff.models import Bill, Transaction, Member, Membership, DailyLog, Onboard_Task, Onboard_Task_Completed, ExitTask, ExitTaskCompleted, Neighborhood
import staff.billing as billing
from staff.views import beginning_of_next_month, first_days_in_months

class UtilsTest(TestCase):
   
   def testMonthlyRanges(self):
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
      self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
      Membership.objects.create(member=self.user1.get_profile(), plan='Resident', start_date=date(2008, 6, 26), rate=settings.RESIDENT_MONTHLY_FEE)

      self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
      Membership.objects.create(member=self.user2.get_profile(), plan='Resident', start_date=date(2008, 6, 26), end_date=(date.today() - timedelta(days=1)), rate=settings.RESIDENT_MONTHLY_FEE)

      self.on_task_1 = Onboard_Task.objects.create(name="Welcome Coffee Mug", order=1, description="Print a coffee mug", monthly_only=True)
      self.on_task_2 = Onboard_Task.objects.create(name="Entry Tat", order=2, description="Tattoo a bar code on the neck.", monthly_only=False)

      self.exit_task_1 = ExitTask.objects.create(name="Exit Shaming", order=1, description="The parade of shame.")
      self.exit_task_2 = ExitTask.objects.create(name="Break Coffee Mug", order=2, description="Crush the member's coffee mug.")


   def testTasks(self):
      self.assertEqual(Onboard_Task_Completed.objects.filter(member=self.user1.profile).count(), 0)
      self.assertEqual(ExitTaskCompleted.objects.filter(member=self.user1.profile).count(), 0)

      self.assertTrue(self.user1.profile in self.on_task_1.uncompleted_members())
      self.assertFalse(self.user2.profile in self.on_task_1.uncompleted_members()) # ended memberships don't require onboard tasks

      Onboard_Task_Completed.objects.create(member=self.user1.profile, task=self.on_task_1)
      self.assertFalse(self.user1.profile in self.on_task_1.uncompleted_members())

      self.assertFalse(self.user1.profile in self.exit_task_1.uncompleted_members())
      self.assertTrue(self.user2.profile in self.exit_task_1.uncompleted_members())

      ExitTaskCompleted.objects.create(member=self.user2.profile, task=self.exit_task_1)
      self.assertFalse(self.user2.profile in self.exit_task_1.uncompleted_members())

class MemberTestCase(TestCase):
   def setUp(self):
      self.neighborhood1 = Neighborhood.objects.create(name="Beggar's Gulch")

      self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
      self.profile1 = self.user1.profile
      self.profile1.neighborhood=self.neighborhood1
      self.profile1.save()
      Membership.objects.create(member=self.user1.get_profile(), plan='Basic', start_date=date(2008, 2, 26), end_date=date(2010, 6, 25), rate=settings.BASIC_MONTHLY_FEE)
      Membership.objects.create(member=self.user1.get_profile(), plan='Resident', start_date=date(2010, 6, 26), rate=settings.RESIDENT_MONTHLY_FEE)

      self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
      self.profile2 = self.user2.profile
      Membership.objects.create(member=self.user2.get_profile(), plan='PT5', start_date=date(2009, 1, 1), rate=settings.PT5_MONTHLY_FEE)

      self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
      self.profile3 = self.user3.profile
      self.profile3.neighborhood=self.neighborhood1
      self.profile3.save()
      self.user3.profile.save()

      self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
      self.profile4 = self.user4.profile
      self.profile4.neighborhood=self.neighborhood1
      self.profile4.save()
      Membership.objects.create(member=self.user4.get_profile(), plan='PT5', start_date=date(2009, 1, 1), end_date=date(2010, 1, 1), rate=settings.PT5_MONTHLY_FEE)


   def testInfoMethods(self):
      self.assertTrue(self.user1.profile in Member.objects.members_by_membership_type('Resident'))
      self.assertFalse(self.user1.profile in Member.objects.members_by_membership_type('Basic'))
      self.assertTrue(self.user2.profile in Member.objects.members_by_membership_type('PT5'))
      self.assertFalse(self.user2.profile in Member.objects.members_by_membership_type('Resident'))

      self.assertTrue(self.user1.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
      self.assertFalse(self.user2.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
      self.assertFalse(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
      self.assertFalse(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1))
      self.assertTrue(self.user3.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))
      self.assertTrue(self.user4.profile in Member.objects.members_by_neighborhood(self.neighborhood1, active_only=False))

class BillingTestCase(TestCase):

   def setUp(self):
      self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
      self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
      self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
      self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')      

      Membership.objects.create(member=self.user1.get_profile(), plan='Resident', start_date=date(2008, 6, 26), rate=settings.RESIDENT_MONTHLY_FEE)
      
      Membership.objects.create(member=self.user2.get_profile(), plan='Resident', start_date=date(2008, 1, 31), rate=settings.RESIDENT_MONTHLY_FEE)

      Membership.objects.create(member=self.user3.get_profile(), plan='PT15', start_date=date(2008, 2, 1), end_date=date(2010, 6, 20), rate=settings.PT15_MONTHLY_FEE)
      Membership.objects.create(member=self.user3.get_profile(), plan='Basic', start_date=date(2010, 6, 21), rate=settings.BASIC_MONTHLY_FEE)
      for day in range(2,19): DailyLog.objects.create(member=self.user3.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

      Membership.objects.create(member=self.user4.get_profile(), plan='PT5', start_date=date(2008, 2, 1), end_date=date(2010, 6, 10), rate=settings.PT5_MONTHLY_FEE)
      Membership.objects.create(member=self.user4.get_profile(), plan='Resident', start_date=date(2010, 6, 11), rate=settings.RESIDENT_MONTHLY_FEE)
      for day in range(2,11): DailyLog.objects.create(member=self.user4.get_profile(), visit_date=date(2010, 6, day), payment='Bill')

   def testMembership(self):
      orig_log = Membership.objects.create(member=self.user1.get_profile(), plan='Resident', start_date=date(2008, 2, 10), rate=475)
      self.assertTrue(orig_log.is_anniversary_day(date(2010, 4, 10)))
      orig_log.end_date = orig_log.start_date + timedelta(days=31)
      orig_log.save()
      new_log = Membership(start_date=orig_log.end_date, member=orig_log.member, plan=orig_log.membership_plan, rate=orig_log.rate)
      self.assertRaises(Exception, new_log.save) # the start date is the same as the previous plan's end date, which is an error
      new_log.start_date = orig_log.end_date + timedelta(days=1)
      new_log.save()
      new_log.end_date = new_log.start_date + timedelta(days=64)
      new_log.start_date = new_log.end_date + timedelta(days=12)
      self.assertRaises(Exception, new_log.save) # the start date can't be the same or later than the end date

   def testRun(self):
      member1 = self.user1.get_profile()
      member2 = self.user2.get_profile()
      member3 = self.user3.get_profile()
      member4 = self.user4.get_profile()

      end_time = datetime(2010, 7, 1)
      day_range = range(40)
      day_range.reverse()
      days = [end_time - timedelta(days=i) for i in day_range]
      # 2010-05-31 through 2010-07-01
      for day in days:
         billing.run_billing(day)
         if day.month == 6 and day.day == 10:
            self.assertTrue(member4.last_bill() != None)
            self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
            self.assertEqual(member4.last_bill().membership, Membership.objects.get(member=member4, plan="PT5"))
            self.assertEqual(member4.last_bill().dropins.count(), 9) # dropins on 6/2 - 6/10
            self.assertEqual(member4.last_bill().amount, (member4.last_bill().dropins.count() - 5) * settings.PT5_DROPIN_FEE)
         if day.month == 6 and day.day == 11:
            self.assertTrue(member4.last_bill() != None)
            self.assertTrue(member4.last_bill().created.month == day.month and member4.last_bill().created.day == day.day)
            self.assertEqual(member4.last_bill().membership, Membership.objects.get(member=member4, plan="Resident"))
            self.assertEqual(member4.last_bill().dropins.count(), 0)

         if day.month == 6 and day.day == 20:
            self.assertTrue(member3.last_bill() != None)
            self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
            self.assertEqual(member3.last_bill().dropins.count(), 17)
            
         if day.month == 6 and day.day == 21:
            self.assertTrue(member3.last_bill() != None)
            self.assertTrue(member3.last_bill().created.month == day.month and member3.last_bill().created.day == day.day)
            self.assertEqual(member3.last_bill().dropins.count(), 0)

         if day.day == 26:
            self.assertTrue(member1.last_membership().is_anniversary_day(day))
            member_bills = member1.bills.all().order_by('-created')
            self.assertTrue(len(member_bills) > 0)
            self.assertTrue(member_bills[0].membership == member1.last_membership())
         if day.month == 6 and day.day == 30:
            self.assertTrue(member2.last_membership().is_anniversary_day(day))

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
