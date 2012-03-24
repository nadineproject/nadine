import traceback
from datetime import datetime, timedelta, date

from django.conf import settings
from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.management import call_command

from staff.models import Member, MembershipPlan, Membership

from interlink.tests.test_utils import create_user
from interlink.models import MailingList, IncomingMail, OutgoingMail
from interlink.mail import DEFAULT_MAIL_CHECKER, TestMailChecker, TEST_INCOMING_MAIL, add_test_incoming

class ListTest(TestCase):

   def setUp(self):
      self.user1, self.client1 = create_user('alice', 'Alice', 'Dodgson', email='alice@example.com', is_staff=True)
      self.user2, self.client2 = create_user('bob', 'Bob', 'Albert', email='bob@example.com')
      self.mlist1 = MailingList.objects.create(
         name='Hat Styles', description='All about les chapeau', subject_prefix='hat',
         email_address='hats@example.com', username='hat', password='1234',
         pop_host='localhost', smtp_host='localhost'
      )

      self.basic_plan = MembershipPlan.objects.create(name='Basic', description='An occasional user', monthly_rate='50', daily_rate='25', dropin_allowance='5', deposit_amount='0')

   def test_subscription_form(self):
      Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.basic_plan, start_date=date.today() - timedelta(days=10))
      self.mlist1.moderators.add(self.user1)
      self.mlist1.subscribers.add(self.user2)
      form_data = {
         'subscribe':'true',
         'mailing_list_id':self.mlist1.id
      }
      response = self.client2.post(reverse('members.views.mail', kwargs={'username':self.user2.username}), form_data)
      self.assertEqual(response.status_code, 302)
      self.assertEqual(IncomingMail.objects.all().count(), 0)
      self.assertEqual(OutgoingMail.objects.all().count(), 1)
      IncomingMail.objects.process_incoming()
      OutgoingMail.objects.send_outgoing()

   def test_moderator_controlled(self):
      self.assertEqual(0, self.mlist1.subscribers.count())
      self.mlist1.moderator_controlled = True
      self.mlist1.save()
      self.mlist1.moderators.add(self.user1)
      self.mlist1.subscribers.add(self.user2)
      self.assertEqual(1, self.mlist1.subscribers.count())

      checker = DEFAULT_MAIL_CHECKER(self.mlist1)

      # check that non-moderator emails are rejected
      add_test_incoming(self.mlist1, 'bob@example.com', 'ahoi 3', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      incoming = checker.fetch_mail()
      self.assertEqual(len(incoming), 1)
      IncomingMail.objects.process_incoming()
      outgoing = OutgoingMail.objects.all()
      self.assertEqual(len(outgoing), 0)
      income = IncomingMail.objects.get(pk=incoming[0].id)
      self.assertEqual(income.state, 'reject')

      add_test_incoming(self.mlist1, 'alice@example.com', 'ahoi 4', 'Who are you. Who who who who.', sent_time=datetime.now() - timedelta(minutes=10))
      incoming = checker.fetch_mail()
      self.assertEqual(len(incoming), 1)
      IncomingMail.objects.process_incoming()
      outgoing = OutgoingMail.objects.all()
      self.assertEqual(len(outgoing), 1)
      income = IncomingMail.objects.get(pk=incoming[0].id)
      self.assertEqual(income.state, 'send')

   def test_opt_out(self):
      self.assertEqual(0, self.mlist1.subscribers.count())
      self.mlist1.is_opt_out = True
      self.mlist1.save()
      user3, client3 = create_user('suz', 'Suz', 'Ebens', email='suz@example.com')
      self.assertEqual(0, self.mlist1.subscribers.count())
      membership = Membership.objects.create(member=user3.get_profile(), membership_plan=self.basic_plan, start_date=date.today() - timedelta(days=31))
      self.assertEqual(1, self.mlist1.subscribers.count())
      self.assertTrue(user3 in self.mlist1.subscribers.all())

      # Now test that subscribership isn't changed if a member is just changing to a new plan
      membership.end_date = date.today() - timedelta(days=1)
      membership.save()
      self.mlist1.subscribers.remove(user3)
      membership2 = Membership.objects.create(member=user3.get_profile(), membership_plan=self.basic_plan, start_date=date.today())
      self.assertFalse(user3 in self.mlist1.subscribers.all())

   def test_subscribe_command(self):
      self.assertEqual(0, Member.objects.active_members().count())
      self.assertEqual(0, self.mlist1.subscribers.count())

      call_command('subscribe_members', '%s' % self.mlist1.id)
      self.assertEqual(0, self.mlist1.subscribers.count())

      Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.basic_plan, start_date=date.today() - timedelta(days=10))
      call_command('subscribe_members', '%s' % self.mlist1.id)
      self.assertEqual(1, self.mlist1.subscribers.count())


   def test_outgoing_processing(self):
      self.assertEqual(OutgoingMail.objects.all().count(), 0)
      OutgoingMail.objects.send_outgoing()
      checker = DEFAULT_MAIL_CHECKER(self.mlist1)

      self.mlist1.subscribers.add(self.user2)
      add_test_incoming(self.mlist1, 'bob@example.com', 'ahoi 3', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      incoming = checker.fetch_mail()
      IncomingMail.objects.process_incoming()
      outgoing = OutgoingMail.objects.all()[0]
      self.assertEqual(outgoing.sent, None)
      OutgoingMail.objects.send_outgoing()
      incoming = IncomingMail.objects.get(pk=incoming[0].id)
      outgoing = OutgoingMail.objects.all()[0]
      self.assertNotEqual(outgoing.sent, None)
      self.assertEqual(incoming.state, 'sent')

   def test_incoming_processing(self):
      checker = DEFAULT_MAIL_CHECKER(self.mlist1)
      # send an email from an unknown address
      add_test_incoming(self.mlist1, 'bogus@example.com', 'ahoi 1', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      incoming = checker.fetch_mail()
      self.assertEqual(len(incoming), 1)
      self.assertEqual(incoming[0].state, 'raw')
      IncomingMail.objects.process_incoming()
      self.assertEqual(OutgoingMail.objects.all().count(), 1)
      incoming = IncomingMail.objects.get(pk=incoming[0].id)
      self.assertEqual(incoming.state, 'moderate')
      outgoing = OutgoingMail.objects.all()[0]
      self.assertEqual(outgoing.original_mail, incoming)
      self.assertTrue(outgoing.subject.startswith('Moderation Request'))

      # send an email from a known address, but not a subscriber
      add_test_incoming(self.mlist1, 'alice@example.com', 'ahoi 2', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      incoming = checker.fetch_mail()
      self.assertEqual(len(incoming), 1)
      self.assertEqual(incoming[0].state, 'raw')
      IncomingMail.objects.process_incoming()
      self.assertEqual(OutgoingMail.objects.all().count(), 2)
      incoming = IncomingMail.objects.get(pk=incoming[0].id)
      self.assertEqual(incoming.state, 'moderate')

      # send an email from a subscriber
      self.mlist1.subscribers.add(self.user2)
      add_test_incoming(self.mlist1, 'bob@example.com', 'ahoi 3', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      incoming = checker.fetch_mail()
      self.assertEqual(len(incoming), 1)
      self.assertEqual(incoming[0].state, 'raw')
      IncomingMail.objects.process_incoming()
      self.assertEqual(OutgoingMail.objects.all().count(), 3)
      incoming = IncomingMail.objects.get(pk=incoming[0].id)
      self.assertEqual(incoming.state, 'send')
      outgoing = OutgoingMail.objects.all()[0]
      self.assertTrue(outgoing.subject.startswith(self.mlist1.subject_prefix), outgoing.subject)

   def test_recipients(self):
      self.assertEqual(len(self.mlist1.subscriber_addresses), 0)
      self.assertEqual(len(self.mlist1.moderator_addresses), 0)
      self.mlist1.subscribers.add(self.user2)
      self.assertEqual(len(self.mlist1.subscriber_addresses), 1)
      self.assertEqual(len(self.mlist1.moderator_addresses), 0)
      self.mlist1.moderators.add(self.user1)
      self.assertEqual(len(self.mlist1.subscriber_addresses), 1)
      self.assertEqual(len(self.mlist1.moderator_addresses), 1)

   def test_mail_checking(self):
      self.assertEqual(DEFAULT_MAIL_CHECKER, TestMailChecker)
      checker = DEFAULT_MAIL_CHECKER(self.mlist1)
      add_test_incoming(self.mlist1, 'alice@example.com', 'ahoi', 'I like traffic lights.', sent_time=datetime.now() - timedelta(minutes=15))
      self.assertEqual(IncomingMail.objects.all().count(), 0)
      in_mail = checker.fetch_mail()
      self.assertEqual(len(in_mail), 1)
      self.assertEqual(in_mail[0].origin_address, 'alice@example.com')
      self.assertEqual(IncomingMail.objects.all().count(), 1)

      add_test_incoming(self.mlist1, 'alice@example.com', 'ahoi 2', 'I like traffic lights A LOT.', sent_time=datetime.now() - timedelta(minutes=15))
      MailingList.objects.fetch_all_mail()
      self.assertEqual(IncomingMail.objects.all().count(), 2)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
