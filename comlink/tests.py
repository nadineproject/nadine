from mailgun_incoming.forms import *
from mailgun_incoming.models import *
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
        """
        
        """
        request = request_factory.post('/', data=testpostdata)
        formk = modelform_factory(IncomingEmail, form=EmailForm, exclude=[])
        form = formk(request.POST)
        email = form.save()

        for k, v in form.field_map.items():
            assert getattr(email, v) == testpostdata[k]






