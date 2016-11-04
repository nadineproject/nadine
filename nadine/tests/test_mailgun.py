import traceback
from datetime import datetime, timedelta, date

from django.test import SimpleTestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from nadine.models import *
from nadine.utils import mailgun

class MailgunTestCase(SimpleTestCase):

    def test_mailgun(self):
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
