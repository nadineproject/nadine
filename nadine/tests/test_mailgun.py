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


# Copyright 2019 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
