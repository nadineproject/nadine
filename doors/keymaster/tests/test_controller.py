from django.test import SimpleTestCase
from django.utils import timezone

#from doors.hid_control import DoorController
from doors.keymaster.models import Keymaster
from doors.core import Messages, EncryptedConnection, CardHolder, Gatekeeper, TestDoorController

class DoorControllerTestCase(SimpleTestCase):
    name = "test controller"
    ip_address = "127.0.0.1"
    username = "username"
    password = "password"
    controller = TestDoorController(name, ip_address, username, password)

    def setUp(self):
        pass

    def test_creation(self):
        self.assertEqual(self.controller.door_name, self.name)
        self.assertEqual(self.controller.door_ip, self.ip_address)
        self.assertEqual(self.controller.door_user, self.username)
        self.assertEqual(self.controller.door_pass, self.password)

    def test_save_cardholder(self):
        self.controller.clear_data()
        self.assertEqual(0, self.controller.cardholder_count())
        cardholder = CardHolder("1", "Jacob", "Sayles", "jacobsayles", "123456")
        self.controller.save_cardholder(cardholder)
        self.assertEqual(1, self.controller.cardholder_count())
        self.controller.clear_data()
        self.assertEqual(0, self.controller.cardholder_count())

    def test_get_cardholder(self):
        cardholder = CardHolder("1", "Jacob", "Sayles", "jacobsayles", "123456")
        self.controller.clear_data()
        self.controller.save_cardholder(cardholder)
        self.assertEqual(cardholder, self.controller.get_cardholder_by_id("1"))
        self.assertEqual(cardholder, self.controller.get_cardholder_by_code("123456"))

    def test_process_codes(self):
        c1 = CardHolder("1", "Jacob", "Sayles", "jacobsayles", "123456")
        c2 = CardHolder("2", "Susan", "Dorsch", "susandorsch", "111111")
        c3 = CardHolder("3", "Bob", "Smith", "bobsmith", "666666")

        self.controller.clear_data()
        self.controller.save_cardholder(c1)  # No Change
        self.controller.save_cardholder(c2)  # Change
        self.controller.save_cardholder(c3) # Delete
        self.assertEqual(3, self.controller.cardholder_count())

        # Process the changes
        new_codes = [
            {'username':'jacobsayles', 'first_name':'Jacob', 'last_name':'Sayles', 'code':'123456'},     # No Change
            {'username':'susandorsch', 'first_name':'Susan', 'last_name':'Dorsch', 'code':'222222'},     # Change
            {'username':'fredjones', 'first_name':'Fred', 'last_name':'Jones', 'code':'7777777'}, # Add
        ]
        changes = self.controller.process_door_codes(new_codes, load_credentials=False)
        self.assertEqual(len(changes), 4)

        for c in changes:
            self.assertNotEqual(c.username, 'jacobsayles')
            if c.username == 'susandorsch':
                if c.code == "111111":
                    self.assertEqual(c.action, 'delete')
                elif c.code == "222222":
                    self.assertEqual(c.action, 'add')
                else:
                    self.fail("user 'susandorsch' has weird data")
            elif c.username == 'bobsmith':
                self.assertEqual(c.action, 'delete')
            elif c.username == 'fredjones':
                self.assertEqual(c.action, 'add')
            else:
                self.fail("Weird data found")


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
