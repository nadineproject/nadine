import json
import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError
from django.utils.timezone import localtime, now

from . import arp
from arpwatch.models import *


class ArpWatchTest(TestCase):

    def test_duplicate_device(self):
        MAC = "AA:AA:AA:AA:AA:AA"
        device1 = UserDevice.objects.create(mac_address=MAC)
        with self.assertRaises(IntegrityError):
            device2 = UserDevice.objects.create(mac_address=MAC)

    # def test_dir_lock(self):
    #     arp.unlock_import_dir()
    #     self.assertFalse(arp.import_dir_locked())
    #     arp.lock_import_dir()
    #     self.assertTrue(arp.import_dir_locked())
    #     arp.unlock_import_dir()
    #     self.assertFalse(arp.import_dir_locked())

    # def test_log_message(self):
    #     arp.unlock_import_dir()
    #     arp.log_message("testing")
    #     self.assertFalse(arp.import_dir_locked())

    def test_arpwatch_for_user(self):
        # Register user1 with device1
        user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        device1 = UserDevice.objects.create(user=user1, device_name="Device One", mac_address="90:A2:DA:00:EE:5D", ignore=False)
        ip1 = "127.0.0.1"

        # Create 5 hours of logs with device1
        s = start = localtime(now()) - timedelta(hours=6)
        end = localtime(now()) - timedelta(hours=1)
        while (s < end):
            ArpLog.objects.create(runtime=s, device=device1, ip_address=ip1)
            s = s + timedelta(minutes=5)

        # Pull the logs for user1 and make sure we have 5 hours worth
        logs = ArpLog.objects.for_user(user1, start, end)
        self.assertEqual(1, len(logs))
        five_hours_in_seconds = 5 * 60 * 60
        self.assertEqual(logs[0].diff.seconds, five_hours_in_seconds)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
