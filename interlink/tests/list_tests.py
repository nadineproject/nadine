import email
import logging

from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.core import mail
from django.utils import timezone

from staff.models import Member, MembershipPlan, Membership

from interlink.tests.test_utils import create_user
from interlink.models import MailingList, IncomingMail, OutgoingMail


class ListTest(TestCase):

	def setUp(self):
		self.user1, self.client1 = create_user('alice', 'Alice', 'Dodgson', email='alice@example.com', is_staff=True)
		self.user2, self.client2 = create_user('bob', 'Bob', 'Albert', email='bob@example.com')
		self.user3, self.client3 = create_user('charlie', 'Charlie', 'Tuna', email='charlie@example.com')
		self.mlist1 = MailingList.objects.create(
			name='Hat Styles', description='All about les chapeau', subject_prefix='hat',
			email_address='hats@example.com', username='hat', password='1234',
			pop_host='localhost', smtp_host='localhost'
		)

		self.basic_plan = MembershipPlan.objects.create(name='Basic', description='An occasional user', monthly_rate='50', daily_rate='25', dropin_allowance='5')

	def test_subscription_form(self):
		Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.basic_plan, start_date=timezone.now().date() - timedelta(days=10))
		self.mlist1.moderators.add(self.user1)
		self.mlist1.subscribers.add(self.user2)
		form_data = {
			'subscribe':'true',
			'mailing_list_id':self.mlist1.id
		}
		response = self.client2.post(reverse('members.views.mail', kwargs={'username':self.user2.username}), form_data)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(IncomingMail.objects.count(), 0)
		self.assertEqual(OutgoingMail.objects.count(), 1)
		IncomingMail.objects.process_incoming()
		OutgoingMail.objects.send_outgoing()

	def test_moderator_controlled(self):
		self.assertEqual(0, self.mlist1.subscribers.count())
		self.mlist1.moderator_controlled = True
		self.mlist1.save()
		self.mlist1.moderators.add(self.user1)
		self.mlist1.subscribers.add(self.user2)
		self.assertEqual(1, self.mlist1.subscribers.count())

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='bob@example.com',
							  subject='ahoi 3',
							  body='I like traffic lights',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))

		IncomingMail.objects.process_incoming()
		outgoing = OutgoingMail.objects.all()
		self.assertEqual(len(outgoing), 0)
		incoming = IncomingMail.objects.get(pk=incoming.id)
		self.assertEqual(incoming.state, 'reject')

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='alice@example.com',
							  subject='ahoi 4',
							  body='Who are you. Who who who who.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=10))

		IncomingMail.objects.process_incoming()
		outgoing = OutgoingMail.objects.all()
		self.assertEqual(len(outgoing), 1)
		income = IncomingMail.objects.get(pk=incoming.id)
		self.assertEqual(income.state, 'send')

	def test_moderated_from(self):
		"Moderated emails from non-users were losing their 'from' address."
		self.mlist1.moderators.add(self.user1)
		self.mlist1.subscribers.add(self.user2)
		self.assertEqual(1, self.mlist1.subscribers.count())

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='unknownperson@example.com',
							  subject='ahoi 3',
							  body='I like traffic lights.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))
		IncomingMail.objects.process_incoming()
		incoming = IncomingMail.objects.get(pk=incoming.pk)
		self.assertEqual(incoming.state, 'moderate')
		# One outgoing mail, the moderation mail
		self.assertEqual(1, OutgoingMail.objects.count())
		# Clear the outgoing mail
		OutgoingMail.objects.all().delete()
		# Approve the moderated mail
		incoming.create_outgoing()
		OutgoingMail.objects.send_outgoing()
		self.assertEqual(1, len(mail.outbox))
		m = mail.outbox[0]
		self.assertEqual('unknownperson@example.com', m.from_email)
		self.assertEqual('hats@example.com', m.extra_headers['Sender'])
		self.assertEqual('unknownperson@example.com', m.extra_headers['Reply-To'])
		
	def test_moderated_subject(self):
		"Moderated emails from non-users were losing their 'from' address."
		self.mlist1.moderators.add(self.user1)
		self.mlist1.subscribers.add(self.user2)
		self.assertEqual(1, self.mlist1.subscribers.count())

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='bob@example.com',
							  subject='This is a freaking auto-reply message',
							  body='just a stupid message that should get bonked',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))
		IncomingMail.objects.process_incoming()
		incoming = IncomingMail.objects.get(pk=incoming.pk)
		self.assertEqual(incoming.state, 'moderate')
		
	def test_opt_out(self):
		self.assertEqual(0, self.mlist1.subscribers.count())
		self.mlist1.is_opt_out = True
		self.mlist1.save()
		user3, _client3 = create_user('suz', 'Suz', 'Ebens', email='suz@example.com')
		self.assertEqual(0, self.mlist1.subscribers.count())
		membership = Membership.objects.create(member=user3.get_profile(), membership_plan=self.basic_plan, start_date=timezone.now().date() - timedelta(days=31))
		self.assertEqual(1, self.mlist1.subscribers.count())
		self.assertTrue(user3 in self.mlist1.subscribers.all())

		# Now test that subscribership isn't changed if a member is just changing to a new plan
		membership.end_date = timezone.now().date() - timedelta(days=1)
		membership.save()
		self.mlist1.subscribers.remove(user3)
		_membership2 = Membership.objects.create(member=user3.get_profile(), membership_plan=self.basic_plan, start_date=timezone.now().date())
		self.assertFalse(user3 in self.mlist1.subscribers.all())

	def test_subscribe_command(self):
		self.assertEqual(0, Member.objects.active_members().count())
		self.assertEqual(0, self.mlist1.subscribers.count())

		call_command('subscribe_members', '%s' % self.mlist1.id)
		self.assertEqual(0, self.mlist1.subscribers.count())

		Membership.objects.create(member=self.user2.get_profile(), membership_plan=self.basic_plan, start_date=timezone.now().date() - timedelta(days=10))
		call_command('subscribe_members', '%s' % self.mlist1.id)
		self.assertEqual(1, self.mlist1.subscribers.count())

	def test_outgoing_processing(self):
		self.assertEqual(OutgoingMail.objects.count(), 0)
		OutgoingMail.objects.send_outgoing()
		self.mlist1.subscribers = [self.user2, self.user3]

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='bob@example.com',
							  subject='ahoi 3',
							  body='I like traffic lights.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))

		IncomingMail.objects.process_incoming()
		outgoing = OutgoingMail.objects.all()[0]
		self.assertIsNone(outgoing.sent)
		self.assertEqual(0, len(mail.outbox))
		OutgoingMail.objects.send_outgoing()
		incoming = IncomingMail.objects.get(pk=incoming.id)
		outgoing = OutgoingMail.objects.all()[0]
		self.assertIsNotNone(outgoing.sent)
		self.assertEqual(incoming.state, 'sent')
		# Only one mail sent the the server, but with multiple BCCs
		self.assertEqual(1, len(mail.outbox))
		m = mail.outbox[0]

		# Inspect the mails --
		# The 'From' should be the user's name & address
		# The 'To' should be the mailing list
		# The 'Sender' should be the mailing list
		# The 'Reply-To' should be the mailing list
		self.assertEqual('Bob Albert <bob@example.com>', m.from_email)
		self.assertEqual('hat ahoi 3', m.subject)
		self.assertEqual(['hats@example.com'], m.to)
		self.assertEqual('hats@example.com', m.extra_headers['Sender'])
		self.assertEqual('Bob Albert <bob@example.com>', m.extra_headers['Reply-To'])
		self.assertEqual([u'bob@example.com', u'charlie@example.com'], sorted(m.recipients()))

	def test_incoming_processing(self):
		# send an email from an unknown address
		self.mlist1.moderators.add(self.user3)
		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='bogus@example.com',
							  subject='ahoi 1',
							  body='I like traffic lights.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))

		self.assertEqual(incoming.state, 'raw')
		IncomingMail.objects.process_incoming()
		self.assertEqual(OutgoingMail.objects.count(), 1)
		incoming = IncomingMail.objects.get(pk=incoming.id)
		self.assertEqual(incoming.state, 'moderate')
		outgoing = OutgoingMail.objects.all()[0]
		self.assertEqual(outgoing.original_mail, incoming)
		self.assertTrue(outgoing.subject.startswith('Moderation Request'))
		# Process outgoing and make sure the moderation email gets sent.
		OutgoingMail.objects.send_outgoing()
		self.assertEqual(1, len(mail.outbox))
		m = mail.outbox[0]
		self.assertEqual('hats@example.com', m.from_email)
		self.assertEqual(u'Moderation Request: Hat Styles: ahoi 1', m.subject)
		self.assertEqual(['charlie@example.com'], m.to)
		self.assertEqual(u'hats@example.com', m.extra_headers['Reply-To'])
		self.assertEqual([u'charlie@example.com'], m.recipients())

		# send an email from a known address, but not a subscriber
		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='alice@example.com',
							  subject='ahoi 1',
							  body='I like traffic lights.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))
		self.assertEqual(incoming.state, 'raw')
		IncomingMail.objects.process_incoming()
		self.assertEqual(OutgoingMail.objects.count(), 2)
		incoming = IncomingMail.objects.get(pk=incoming.id)
		self.assertEqual(incoming.state, 'moderate')

		# send an email from a subscriber
		self.mlist1.subscribers.add(self.user2)

		incoming = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address='bob@example.com',
							  subject='ahoi 3',
							  body='I like traffic lights.',
							  sent_time=timezone.localtime(timezone.now()) - timedelta(minutes=15))

		self.assertEqual(incoming.state, 'raw')
		IncomingMail.objects.process_incoming()
		self.assertEqual(OutgoingMail.objects.count(), 3)
		incoming = IncomingMail.objects.get(pk=incoming.id)
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

	def test_propagate_message_id(self):
		TEST_EMAIL="""From nobody Thu May  3 13:31:54 2012
Date: Thu, 3 May 2012 13:27:29 -0700
From: Bob Albert <bob@example.com>
To: hats@example.com
Message-ID: <00A46A5C1AF8411DB6FF0CB15688E828@gmail.com>
Subject: Test me
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="4fa2ea31_5046b5a9_1b6"

--4fa2ea31_5046b5a9_1b6
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Content-Disposition: inline

Please ignore=E2=80=A6 =20


--4fa2ea31_5046b5a9_1b6
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Content-Disposition: inline


					 <div>Please ignore=E2=80=A6
					 </div><div><br></div>
					 <div></div>

--4fa2ea31_5046b5a9_1b6--

"""
		self.mlist1.subscribers = [self.user2, self.user3]

		self.mlist1.create_incoming(email.message_from_string(TEST_EMAIL))
		IncomingMail.objects.process_incoming()
		OutgoingMail.objects.send_outgoing()

		self.assertEqual(1, len(mail.outbox))
		m = mail.outbox[0]
		self.assertEqual('Bob Albert <bob@example.com>', m.from_email)
		self.assertEqual('hat Test me', m.subject)
		self.assertEqual(['hats@example.com'], m.to)
		self.assertEqual('<00A46A5C1AF8411DB6FF0CB15688E828@gmail.com>', m.extra_headers['Message-ID'])

	def test_reply_subject(self):
		"Replies don't have the subject prefix prefixed, if it begins with re prefix"
		TEST_EMAIL = """From nobody Thu May	 3 14:47:44 2012
Date: Thu, 3 May 2012 14:47:29 -0700
From: Bob Albert <bob@example.com>
To: Charlie Tuna <charlie@example.com>
Cc: hats@example.com
Message-ID: <5468B39B3E1548269FF218E1716B93A3@gmail.com>
In-Reply-To: <66A138E298054C28B6FBF7E6704C36E2@gmail.com>
References: <66A138E298054C28B6FBF7E6704C36E2@gmail.com>
Subject: Re: hat Reply
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="4fa2fcf1_759f82cd_1b6"

--4fa2fcf1_759f82cd_1b6
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Content-Disposition: inline

I want to reply to this email... =20


On Thursday, May 3, 2012 at 2:47 PM, Paul Watts wrote:

> I am sending this email=E2=80=A6 =20
> =20
> =20


--4fa2fcf1_759f82cd_1b6
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Content-Disposition: inline


					 <div>
						  I want to reply to this email...
					 </div>
					 <div></div>
					 =20
					 <p style=3D=22color: =23A0A0A8;=22>On Thursday, May 3, 20=
12 at 2:47 PM, Paul Watts wrote:</p>
					 <blockquote type=3D=22cite=22 style=3D=22border-left-styl=
e:solid;border-width:1px;margin-left:0px;padding-left:10px;=22>
						  <span><div><div>
					 <div>
						  I am sending this email=E2=80=A6
					 </div><div><br></div>
					 </blockquote>
					 =20
					 <div>
						  <br>
					 </div>

--4fa2fcf1_759f82cd_1b6--

"""
		self.mlist1.subscribers = [self.user2, self.user3]

		self.mlist1.create_incoming(email.message_from_string(TEST_EMAIL))
		IncomingMail.objects.process_incoming()
		OutgoingMail.objects.send_outgoing()

		self.assertEqual(1, len(mail.outbox))
		m = mail.outbox[0]
		self.assertEqual('Bob Albert <bob@example.com>', m.from_email)
		self.assertEqual('Re: hat Reply', m.subject)
		self.assertEqual(['hats@example.com'], m.to)
		self.assertEqual('<5468B39B3E1548269FF218E1716B93A3@gmail.com>', m.extra_headers['Message-ID'])
		self.assertEqual('<66A138E298054C28B6FBF7E6704C36E2@gmail.com>', m.extra_headers['In-Reply-To'])
		self.assertEqual('<66A138E298054C28B6FBF7E6704C36E2@gmail.com>', m.extra_headers['References'])

	def test_no_content_type(self):
		TEST_EMAIL = """Return-Path: <store@b-pb-mailstore-quonix>
Delivered-To: members@officenomads.com
Date: 8 Jun 2012 17:26:08 -0000
Message-ID: <1339176368.11152.blah>
Delivered-To: Autoresponder
To: members@officenomads.com
From: test@testington.com
Subject: Friday June 8th-out of office

This email has no content type
"""
		self.mlist1.subscribers = [self.user2, self.user3]
		self.mlist1.create_incoming(email.message_from_string(TEST_EMAIL))

	def _throttle_logging_handler(self):
		logger = logging.getLogger("interlink.models")
		hdlr = logging.NullHandler()
		logger.addHandler(hdlr)

	def test_throttle_limit(self):
		# Squelch the throttle warning
		self._throttle_logging_handler()

		self.mlist1.subscribers = [self.user2, self.user3]
		self.mlist1.throttle_limit = 5
		self.mlist1.save()

		# Create mail A that will go through
		incoming1 = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address=self.user2.email,
							  subject='ahoi 1',
							  body='This will go through',
							  sent_time=timezone.localtime(timezone.now()))

		IncomingMail.objects.process_incoming()
		OutgoingMail.objects.send_outgoing()
		self.assertEqual(1, len(mail.outbox))

		# Create two more -- #2 will go through, #3 will not.
		_incoming2 = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address=self.user2.email,
							  subject='ahoi 2',
							  body='This will go through as well',
							  sent_time=timezone.localtime(timezone.now()))
		_incoming3 = IncomingMail.objects.create(mailing_list=self.mlist1,
							  origin_address=self.user2.email,
							  subject='ahoi 3',
							  body='This will NOT go through',
							  sent_time=timezone.localtime(timezone.now()))
		IncomingMail.objects.process_incoming()
		OutgoingMail.objects.send_outgoing()
		self.assertEqual(2, len(mail.outbox))

		# Even if we try to call send_outgoing again, this
		# won't go through.
		OutgoingMail.objects.send_outgoing()
		self.assertEqual(2, len(mail.outbox))

		#
		# Change #1 send time to be earlier (beyond the hour)
		# Send again -- this time #3 will go through
		outgoing1 = OutgoingMail.objects.get(original_mail=incoming1)
		outgoing1.sent = timezone.localtime(timezone.now()) - timedelta(hours=2)
		outgoing1.save()

		OutgoingMail.objects.send_outgoing()
		self.assertEqual(3, len(mail.outbox))


# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
