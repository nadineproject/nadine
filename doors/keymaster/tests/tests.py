import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.utils import timezone

from doors.keymaster.models import Keymaster
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
