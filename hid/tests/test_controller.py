from django.test import SimpleTestCase
from django.utils import timezone

from hid.hid_control import DoorController
from hid.models import Messages, EncryptedConnection, Keymaster, Gatekeeper

class DoorControllerTestCase(SimpleTestCase):
    def setup(self):
        pass

    def test_creation(self):
        ip_address = "127.0.0.1"
        username = "username"
        password = "password"
        dc = DoorController(ip_address, username, password)
        self.assertEqual(dc.door_ip, ip_address)
        self.assertEqual(dc.door_user, username)
        self.assertEqual(dc.door_pass, password)