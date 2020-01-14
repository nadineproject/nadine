from django.forms.models import modelform_factory
from django.test import RequestFactory
from django.test import TestCase, SimpleTestCase

from comlink import mailgun
from comlink.mailgun import MailgunAPI, MailgunMessage
from comlink.forms import *
from comlink.models import *


request_factory = RequestFactory()


testpostdata = {
    'sender': "joeblogs@gmail.com",
    'from': "joeblogs@gmail.com",
    'message-headers': "fooobar",
    'stripped-html': "fooobar",
    'stripped-signature': "fooobar",
    'content-id-map': "fooobar",
    'body-plain': "fooobar",
    'stripped-text': "fooobar",
    'body-html': "fooobar",
    'recipient': "sall@example.com",
    'subject': "Spam",
}


class SimpleTest(TestCase):

    def test_saving_inbound_email(self):
        request = request_factory.post('/', data=testpostdata)
        formk = modelform_factory(EmailMessage, form=EmailForm, exclude=[])
        form = formk(request.POST)
        email = form.save()

        for k, v in list(form.field_map.items()):
            assert getattr(email, v) == testpostdata[k]


class MailingListTest(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='alice', first_name='Alice', last_name='Dodgson', email='alice@example.com', is_staff=True)
        self.user2= User.objects.create(username='bob', first_name='Bob', last_name='Albert', email='bob@example.com')
        self.user3= User.objects.create(username='charlie', first_name='Charlie', last_name='Tuna', email='charlie@example.com')

        self.list1 = MailingList.objects.create(
            name='Hat Styles',
            subject_prefix='hat',
            address='hats@example.com',
        )

    def test_subscribe_unsubscribe(self):
        self.assertEqual(0, self.list1.subscribers.count())
        self.list1.subscribe(self.user1)
        self.assertEqual(1, self.list1.subscribers.count())
        self.list1.unsubscribe(self.user1)
        self.assertEqual(0, self.list1.subscribers.count())
        self.assertEqual(1, self.list1.unsubscribed.count())


class MailgunMessageTestCase(SimpleTestCase):
    bob_email = "bob@bob.net"
    bob = "Bob Smith <%s>" % bob_email
    alice_email = "alice@312main.ca"
    alice = "Alice Smith <%s>" % alice_email
    frank_email = "frank@example.com"
    frank = "Frank Smith <%s>" % frank_email
    mailgun_data = {'from':bob,
        'subject': "This is a test",
        'to':[alice, frank, bob],
        'cc':[frank, alice, bob],
        'bcc':[bob, alice, frank],
    }

    def get_sample_message(self):
        """Return a message with everyone in the TO, CC, and BCC."""
        message = MailgunMessage(self.bob, self.alice, "Test Subject", body_text="this is a test")
        message.add_to(self.frank)
        message.add_to(self.bob)
        message.add_cc(self.frank)
        message.add_cc(self.alice)
        message.add_cc(self.bob)
        message.add_bcc(self.bob)
        message.add_bcc(self.alice)
        message.add_bcc(self.frank)
        return message

    def test_address_map(self):
        message = self.get_sample_message()
        addresses = message._address_map('BUNK', [])
        self.assertEqual(addresses, {})

        exclude = []
        addresses = message._address_map('to', exclude)
        self.assertEqual(len(addresses), 3)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)
        self.assertEqual(self.bob_email, list(addresses.keys())[2], exclude)

        exclude = [self.bob_email]
        addresses = message._address_map('to', exclude)
        self.assertEqual(len(addresses), 2)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)

    def test_clean_data(self):
        message = self.get_sample_message()
        clean_data = message._clean_data()
        tos = clean_data['to']
        self.assertEqual(len(tos), 1)
        self.assertEqual(tos[0], self.alice)
        ccs = clean_data['cc']
        self.assertEqual(len(ccs), 0)
        bccs = clean_data['bcc']
        self.assertEqual(len(bccs), 1)
        self.assertEqual(bccs[0], self.frank)

    def test_cc(self):
        # Construct a message with the FROM and TO in the CC
        frm = "from@example.com"
        to = "to@example.com"
        cc = "cc@example.com"
        message = MailgunMessage(frm, to, "Test Subject", body_text="this is a test")
        message.add_cc(frm)
        message.add_cc(to)
        message.add_cc(cc)

        # Make sure the FROM and TO got stripped out of the CC
        cc_list = message.get_mailgun_data()["cc"]
        self.assertEqual(1, len(cc_list))
        self.assertTrue(cc in cc_list)
        self.assertFalse(to in cc_list)
        self.assertFalse(frm in cc_list)

    def test_bcc(self):
        # Construct a message with the FROM and TO in the BCC
        frm = "from@example.com"
        to = "to@example.com"
        bcc = "bcc@example.com"
        message = MailgunMessage(frm, to, "Test Subject", body_text="this is a test")
        message.add_bcc(frm)
        message.add_bcc(to)
        message.add_bcc(bcc)

        # Make sure the FROM and TO got stripped out of the BCC
        bcc_list = message.get_mailgun_data()["bcc"]
        self.assertEqual(1, len(bcc_list))
        self.assertTrue(bcc in bcc_list)
        self.assertFalse(to in bcc_list)
        self.assertFalse(frm in bcc_list)

    def test_multiple_to(self):
        # Construct a message with the FROM and another email are in TO
        frm = "from@example.com"
        to = "to@example.com"
        to2 = "to2@example.com"
        cc = "cc@example.com"
        bcc = "bcc@example.com"
        message = MailgunMessage(frm, to, "Test Subject", body_text="this is a test")
        message.add_to(frm)
        message.add_to(to2)
        message.add_cc(cc)
        message.add_bcc(bcc)

        # Make sure CC and BCC didn't get removed
        mailgun_data = message.get_mailgun_data()
        self.assertEqual(1, len(mailgun_data["cc"]))
        self.assertTrue(cc in mailgun_data["cc"])
        self.assertEqual(1, len(mailgun_data["bcc"]))
        self.assertTrue(bcc in mailgun_data["bcc"])

        # Make sure TO, TO2 is in TO and FROM is not
        self.assertEqual(2, len(mailgun_data["to"]))
        self.assertTrue(to in mailgun_data["to"])
        self.assertTrue(to2 in mailgun_data["to"])
        self.assertFalse(frm in mailgun_data["to"])


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
