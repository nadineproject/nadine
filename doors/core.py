import json
import logging
import requests
from datetime import datetime, time, date, timedelta

from keymaster import hid_control
from keymaster.hid_control import DoorController
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    PULL_CONFIGURATION = "pull_configuration"
    PULL_DOOR_CODES = "pull_door_codes"
    FORCE_SYNC = "force_sync"
    MARK_SUCCESS = "mark_success"
    SUCCESS_RESPONSE = "OK"



class DoorTypes(object):
    HID = "hid"
    MAYPI = "maypi"
    
    CHOICES = (
        (HID, "Hid Controller"),
        (MAYPI, "Maypi Controller"),
    )


class DoorEventTypes(object):
    UNKNOWN = "0"
    UNRECOGNIZED = "1"
    GRANTED = "2"
    DENIED = "3"
    LOCKED = "4"
    UNLOCKED = "5"
    
    CHOICES = (
        (UNKNOWN, 'Unknown Command'),
        (UNRECOGNIZED, 'Unrecognized Card'),
        (GRANTED, 'Access Granted'),
        (DENIED, 'Access Denied'),
        (LOCKED, 'Door Locked'),
        (UNLOCKED, 'Door Unlocked'),
    )


class EncryptedConnection(object):
    def __init__(self, encryption_key, keymaster_url=None, ttl=600):
        if not encryption_key:
            raise Exception("Missing Encryption Key")
        self.encryption_key = encryption_key
        self.farnet = Fernet(bytes(encryption_key))
        self.ttl = ttl
        self.keymaster_url = keymaster_url

    def decrypt_message(self, message):
        return self.farnet.decrypt(bytes(message), ttl=self.ttl)

    def encrypt_message(self, message):
        return self.farnet.encrypt(bytes(message))

    def send_message(self, message):
        # Encrypt the message
        encrypted_message = self.encrypt_message(message)
        
        # Send the message 
        response = requests.post(self.keymaster_url, data={'message':encrypted_message})
        
        # Process the response
        response_json = response.json()
        if 'error' in response_json:
            error = response_json['error']
            raise Exception(error)

        if 'message' in response_json:
            encrypted_return_message = response.json()['message']
            return self.decrypt_message(encrypted_return_message)

        return None

    def receive_message(self, request):
        # Encrypted message is in 'message' POST variable
        if not request.method == 'POST':
            raise Exception("Must be POST")
        if not 'message' in request.POST:
            raise Exception("No message in POST")
        encrypted_message = request.POST['message']
        return self.decrypt_message(encrypted_message)


class Door(object):
    def __init__(self, name, door_type, ip_address, username, password):
        self.name = name
        self.door_type = door_type
        self.ip_address = ip_address
        self.username = username
        self.password = password

    def get_controller(self):
        if not 'controller' in self.__dict__:
            if self.door_type == DoorTypes.HID:
                self.controller = DoorController(self.ip_address, self.username, self.password)
            else:
                raise NotImplementedError
        return self.controller
    
    def test_connection(self):
        controller = self.get_controller()
        controller.test_connection()
        
    def sync_clock(self):
        controller = self.get_controller()
        set_time_xml = hid_control.set_time()
        controller.send_xml(set_time_xml)
    
    def load_credentials(self): 
        controller = self.get_controller()
        controller.load_credentials()
    
    def process_door_codes(self, doorcode_json):
        controller = self.get_controller()
        changes = controller.process_door_codes(doorcode_json)
        logger.debug("Changes: %s: " % changes)
        controller.process_changes(changes)


class Gatekeeper(object):
    def __init__(self, encrypted_connection):
        self.encrypted_connection = encrypted_connection

    def configure_doors(self, configuration, test_connection=False):
        self.doors = {}
        config_json = json.loads(configuration)
        logger.debug("Configuration: %s" % config_json)
        for d in config_json:
            name = d['name']
            door = Door(name=name, door_type= d['door_type'], ip_address=d['ip_address'], username=d['username'], password=d['password'])
            self.doors[name] = door
            if test_connection:
                door.test_connection()

    def sync_clocks(self):
        for door in self.get_doors().values():
            door.sync_clock()

    def load_data(self):
        for door in self.get_doors().values():
            door.load_credentials()

    def get_doors(self):
        if not 'doors' in self.__dict__:
            raise Exception("Doors not configured")
        return self.doors

    def get_door(self, door_name):
        if 'door_name' not in self.get_doors():
            raise Exception("Door not found")
        return self.doors[door_name]

    def process_door_codes(self, door_codes, all=False):
        doorcode_json = json.loads(door_codes)
        logger.debug(doorcode_json)
        for door in self.get_doors().values():
            door.process_door_codes(doorcode_json)

    def __str__(self): 
        return self.description
