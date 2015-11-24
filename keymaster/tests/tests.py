import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.utils import timezone

from keymaster.models import Messages, EncryptedConnection, Keymaster, Gatekeeper

from cryptography.fernet import Fernet

class EncryptedConnectionTestCase(TestCase):

    def test_encryption(self):
        key = Fernet.generate_key()
        connection = EncryptedConnection(key)
        message = "This is a test"
        encrypted_message = connection.encrypt_message(message)
        decrypted_message = connection.decrypt_message(encrypted_message)
        self.assertEqual(message, decrypted_message)


class KeymasterTestCase(TestCase):
    def setUp(self):
        self.ip_address = "127.0.0.1"
        new_key = Fernet.generate_key()
        Gatekeeper.objects.create(ip_address=self.ip_address, encryption_key=new_key, is_enabled=True)

    def test_handshake(self):
        message = Messages.TEST_QUESTION
        gatekeeper = Gatekeeper.objects.by_ip(self.ip_address)
        keymaster = Keymaster(gatekeeper)
        response = keymaster.process_message(message)
        self.assertEqual(response, Messages.TEST_RESPONSE)

    def test_mark_success(self):
        start_ts = timezone.now()
        gatekeeper = Gatekeeper.objects.by_ip(self.ip_address)
        self.assertTrue(gatekeeper.sync_ts == None)
        message = Messages.MARK_SUCCESS
        keymaster = Keymaster(gatekeeper)
        response = keymaster.process_message(message)
        self.assertEqual(response, Messages.SUCCESS_RESPONSE)
        self.assertFalse(gatekeeper.sync_ts == None)
        self.assertTrue(gatekeeper.sync_ts > start_ts)
