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


# Copyright 2019 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
