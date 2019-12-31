from comlink.forms import *
from comlink.models import *
from django.forms.models import modelform_factory
from django.test import RequestFactory
from django.test import TestCase

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


# Copyright 2019 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
