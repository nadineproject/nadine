from comlink.forms import *
from comlink.models import *
from django.forms.models import modelform_factory
from django.test import RequestFactory
from django.test import TestCase, SimpleTestCase

from comlink import mailgun


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
        formk = modelform_factory(IncomingEmail, form=EmailForm, exclude=[])
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


class MailgunTestCase(SimpleTestCase):
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

    def test_address_map(self):
        addresses = mailgun.address_map(self.mailgun_data, 'BUNK', [])
        self.assertEqual(addresses, {})

        exclude = []
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 3)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)
        self.assertEqual(self.bob_email, list(addresses.keys())[2], exclude)

        exclude = [self.bob_email]
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 2)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)

    def test_clean_mailgun_data(self):
        clean_data = mailgun.clean_mailgun_data(self.mailgun_data)
        # print(clean_data)
        tos = clean_data['to']
        self.assertEqual(len(tos), 1)
        self.assertEqual(tos[0], self.alice)
        ccs = clean_data['cc']
        self.assertEqual(len(ccs), 0)
        bccs = clean_data['bcc']
        self.assertEqual(len(bccs), 1)
        self.assertEqual(bccs[0], self.frank)

    def test_simple(self):
        mailgun_data = {"from": "from@example.com",
            "to": ["to@example.com", ],
            "subject": "subject",
            "text": "This is text content",
            "html": "<p>This is <em>HTML</em> content</p>",
        }
        mailgun.clean_mailgun_data(mailgun_data)
        self.assertEqual("from@example.com", mailgun_data["from"])
        self.assertEqual("subject", mailgun_data["subject"])
        self.assertEqual("This is text content", mailgun_data["text"])
        self.assertEqual("<p>This is <em>HTML</em> content</p>", mailgun_data["html"])
        to_list = mailgun_data["to"]
        self.assertEqual(1, len(to_list))
        self.assertEqual("to@example.com", to_list[0])
        self.assertEqual(mailgun_data['cc'], [])
        self.assertEqual(mailgun_data['bcc'], [])

    def test_bcc(self):
        mailgun_data = {"from": "from@example.com",
            "to": ["to@example.com", ],
            "bcc": ["bcc@example.com", "to@example.com", "from@example.com"],
            "subject": "subject",
            "text": "This is text content",
        }
        mailgun.clean_mailgun_data(mailgun_data)
        bcc_list = mailgun_data["bcc"]
        self.assertEqual(1, len(bcc_list))
        self.assertTrue("bcc@example.com" in bcc_list)
        self.assertFalse("to@example.com" in bcc_list)
        self.assertFalse("from@example.com" in bcc_list)
        self.assertEqual(mailgun_data['cc'], [])

    def test_cc(self):
        mailgun_data = {"from": "from@example.com",
            "to": ["to@example.com", ],
            "cc": ["cc@example.com", "to@example.com", "from@example.com"],
            "subject": "subject",
            "text": "This is text content",
        }
        mailgun.clean_mailgun_data(mailgun_data)
        cc_list = mailgun_data["cc"]
        self.assertEqual(1, len(cc_list))
        self.assertTrue("cc@example.com" in cc_list)
        self.assertFalse("to@example.com" in cc_list)
        self.assertFalse("from@example.com" in cc_list)
        self.assertEqual(mailgun_data['bcc'], [])

    def test_multiple_to(self):
        mailgun_data = {"from": "from@example.com",
            "to": ["to@example.com", "from@example.com", "to2@example.com"],
            "cc": ["cc@example.com"],
            "bcc": ["bcc@example.com"],
            "subject": "subject",
            "text": "This is text content",
        }
        mailgun.clean_mailgun_data(mailgun_data)
        self.assertEqual(1, len(mailgun_data["cc"]))
        self.assertTrue("cc@example.com" in mailgun_data["cc"])

        self.assertEqual(1, len(mailgun_data["bcc"]))
        self.assertTrue("bcc@example.com" in mailgun_data["bcc"])

        self.assertEqual(2, len(mailgun_data["to"]))
        self.assertTrue("to@example.com" in mailgun_data["to"])
        self.assertTrue("to2@example.com" in mailgun_data["to"])
        self.assertFalse("from@example.com" in mailgun_data["to"])


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
