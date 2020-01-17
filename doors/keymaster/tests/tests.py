import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.utils import timezone

from doors.keymaster.models import Keymaster, GatekeeperLog
from doors.core import Messages, EncryptedConnection, Gatekeeper

from cryptography.fernet import Fernet


class EncryptedConnectionTestCase(TestCase):

    def test_encryption(self):
        key = Fernet.generate_key()
        connection = EncryptedConnection(key)
        message = "This is a test"
        encrypted_message = connection.encrypt_message(message)
        decrypted_message = connection.decrypt_message(encrypted_message)
        self.assertNotEqual(message, encrypted_message)
        self.assertEqual(message, decrypted_message)


class KeymasterTestCase(TestCase):

    def setUp(self):
        self.ip_address = "127.0.0.1"
        new_key = Fernet.generate_key()
        Keymaster.objects.create(gatekeeper_ip=self.ip_address, encryption_key=new_key, is_enabled=True)

    def test_mark_success(self):
        start_ts = timezone.now()
        keymaster = Keymaster.objects.by_ip(self.ip_address)
        self.assertTrue(keymaster.success_ts == None)
        keymaster.mark_success()
        self.assertFalse(keymaster.success_ts == None)
        self.assertTrue(keymaster.success_ts > start_ts)

    def test_mark_sync(self):
        start_ts = timezone.now()
        keymaster = Keymaster.objects.by_ip(self.ip_address)
        self.assertTrue(keymaster.sync_ts == None)
        keymaster.mark_sync()
        self.assertFalse(keymaster.sync_ts == None)
        self.assertTrue(keymaster.sync_ts > start_ts)

    def test_is_syncing(self):
        keymaster = Keymaster.objects.by_ip(self.ip_address)
        self.assertFalse(keymaster.is_syncing)
        door_codes = keymaster.pull_door_codes()
        self.assertTrue(keymaster.is_syncing)
        keymaster.mark_sync()
        self.assertFalse(keymaster.is_syncing)

    def test_log_message(self):
        keymaster = Keymaster.objects.by_ip(self.ip_address)
        log_count = GatekeeperLog.objects.filter(keymaster=keymaster).count()
        msg = "This is a test!"
        keymaster.log_message(msg)
        new_log_count = GatekeeperLog.objects.filter(keymaster=keymaster).count()
        self.assertTrue(new_log_count == log_count + 1)
        new_log = GatekeeperLog.objects.filter(keymaster=keymaster).reverse().first()
        self.assertEqual(new_log.message, msg)


class GatekeeperTestCase(TestCase):
    def get_config(self):
        return {
            "CARD_SECRET": Fernet.generate_key().decode("utf-8"),
            "KEYMASTER_SECRET": Fernet.generate_key().decode("utf-8"),
            "KEYMASTER_URL": "http://127.0.0.1:8000/doors/keymaster/",
        }

    def test_config(self):
        # Test a bad config and expect an exception
        bad_config = {}
        with self.assertRaises(Exception) as cm:
            gatekeeper = Gatekeeper(bad_config)

        # Test a good config and expect no exceptions
        try:
            good_config = self.get_config()
            gatekeeper = Gatekeeper(good_config)
        except Exception:
            self.fail("raised Exception unexpectedly!")

        # def test_encode_decode(self):
        #     good_config = self.get_config()
        #     gatekeeper = Gatekeeper(good_config)
        #     o = "this is a test"
        #     e = gatekeeper.encode_door_code(o)
        #     self.assertFalse(o == e)
        #     d = gatekeeper.decode_door_code(e)
        #     self.assertFalse(d == e)
        #     self.assertTrue(d == o)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
