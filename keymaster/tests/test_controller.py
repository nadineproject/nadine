from django.test import SimpleTestCase
from django.utils import timezone

from keymaster.hid_control import DoorController
from keymaster.models import Messages, EncryptedConnection, Keymaster, Gatekeeper

class DoorControllerTestCase(SimpleTestCase):
    ip_address = "127.0.0.1"
    username = "username"
    password = "password"
    controller = DoorController(ip_address, username, password)
    
    def setup(self):
        pass

    def test_creation(self):
        self.assertEqual(self.controller.door_ip, self.ip_address)
        self.assertEqual(self.controller.door_user, self.username)
        self.assertEqual(self.controller.door_pass, self.password)
    
    def test_process_codes(self):
        self.controller.clear_data()
        self.controller.save_cardholder({"cardholderID":"1", "username":"jacob", "forname":"Jacob", "surname":"Sayles", "cardNumber":"123456"})  # No Change
        self.controller.save_cardholder({"cardholderID":"2", "username":"susan", "forname":"Susan", "surname":"Dorsch", "cardNumber":"111111"})  # Change
        self.controller.save_cardholder({"cardholderID":"3", "username":"bob_smith", "forname":"Bob", "surname":"Smith", "cardNumber":"666666"}) # Delete
        new_codes = [
            {'username':'jacob', 'first_name':'Jacob', 'last_name':'Sayles', 'code':'123456'},     # No Change
            {'username':'susan', 'first_name':'Susan', 'last_name':'Dorsch', 'code':'222222'},     # Change
            {'username':'fred_jones', 'first_name':'Fred', 'last_name':'Jones', 'code':'7777777'}, # Add
        ]
        
        # Process the changes
        changes = self.controller.process_door_codes(new_codes, load_credentials=False)
        self.assertEqual(len(changes), 3)
        for change in changes:
            username = change['username']
            action = change['action']
            self.assertNotEqual(username, 'jacob')
            if username == 'susan':
                self.assertEqual(action, 'change')
            elif username == 'bob_smith':
                self.assertEqual(action, 'delete')
            elif username == 'first_name':
                self.assertEqual(action, 'add')