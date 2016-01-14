import json
import logging
import requests
import traceback
from datetime import datetime, time, date, timedelta

import hid_control
from hid_control import DoorController
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    PULL_CONFIGURATION = "pull_configuration"
    CHECK_DOOR_CODES = "check_door_codes"
    PULL_DOOR_CODES = "pull_door_codes"
    PUSH_EVENT_LOGS = "push_event_logs"
    NEW_DATA = "new_data"
    NO_NEW_DATA = "no_new_data"
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
        self.message = None
        self.data = None

    def decrypt_message(self, message):
        return self.farnet.decrypt(bytes(message), ttl=self.ttl)

    def encrypt_message(self, message):
        return self.farnet.encrypt(bytes(message))

    def send_message(self, message, data=None):
        # Encrypt the message
        encrypted_message = self.encrypt_message(message)
        
        # Send the message
        request_package = {'message':encrypted_message}
        if data:
            request_package['data'] = self.encrypt_message(data)
        #print "request: %s" % request_package
        response = requests.post(self.keymaster_url, data=request_package)
        
        # Process the response
        response_json = response.json()
        if 'error' in response_json:
            error = response_json['error']
            traceback.print_exc()
            raise Exception(error)

        if 'message' in response_json:
            encrypted_return_message = response.json()['message']
            return self.decrypt_message(encrypted_return_message)

        return None

    def receive_message(self, request):
        logger.debug("receive_message: %s" % request)
        
        # Encrypted message is in 'message' POST variable
        if not request.method == 'POST':
            raise Exception("Must be POST")
        if not 'message' in request.POST:
            raise Exception("No message in POST")
        encrypted_message = request.POST['message']
        logger.debug("Encrypted message: %s" % encrypted_message)
        self.message = self.decrypt_message(encrypted_message)
        logger.debug("Decrypted message: %s" % self.message)
        
        # Encrypted data is in 'data' POST variable
        if 'data' in request.POST:
            encrypted_data = request.POST['data']
            decrypted_data = self.decrypt_message(encrypted_data)
            self.data = json.loads(decrypted_data)
        
        return self.message


class Door(object):
    def __init__(self, name, door_type, ip_address, username, password, last_event_ts):
        self.name = name
        self.door_type = door_type
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.last_event_ts = last_event_ts

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
    
    def pull_event_logs(self, record_count=100):
        controller = self.get_controller()
        return controller.pull_events(record_count)


class Gatekeeper(object):
    def __init__(self, encrypted_connection):
        self.encrypted_connection = encrypted_connection

    def test_keymaster_connection(self):
        response = self.encrypted_connection.send_message(Messages.TEST_QUESTION)
        if not response == Messages.TEST_RESPONSE:
            raise Exception("Could not connect to Keymaster")

    def configure_doors(self):
        print "Gatekeeper: Pulling door configuration..."
        self.doors = {}
        configuration = self.encrypted_connection.send_message(Messages.PULL_CONFIGURATION)
        config_json = json.loads(configuration)
        logger.debug("Configuration: %s" % config_json)
        for d in config_json:
            name = d.get('name')
            door = Door(name=name,
                        door_type= d.get('door_type'),
                        ip_address=d.get('ip_address'),
                        username=d.get('username'),
                        password=d.get('password'),
                        last_event_ts = d.get('last_event_ts'),
                   )
            logger.debug("Gatekeeper: Loading credentials for '%s'" % name)
            door.load_credentials()
            self.doors[name] = door

    def sync_clocks(self):
        print "Gatekeeper: Syncing the door clocks..."
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
        if door_name not in self.get_doors():
            raise Exception("Door not found")
        return self.doors[door_name]

    def pull_door_codes(self):
        print "Gatekeeper: Pulling door codes..."
        response = self.encrypted_connection.send_message(Messages.PULL_DOOR_CODES)
        doorcode_json = json.loads(response)
        logger.debug(doorcode_json)
        for door in self.get_doors().values():
            door.process_door_codes(doorcode_json)

    def pull_event_logs(self, record_count=100):
        print "Gatekeeper: Pulling event logs..."
        event_logs = {}
        for door_name, door in self.get_doors().items():
            print "Gatekeeper: Pulling %d logs from '%s'" % (record_count, door_name)
            door_logs = door.pull_event_logs(record_count)
            event_logs[door_name] = door_logs
        return event_logs

    def push_event_logs(self, record_count=100):
        print "Gatekeeper: Pushing event logs to keymaster..."
        event_logs = self.pull_event_logs(record_count)
        json_data = json.dumps(event_logs)
        response = self.encrypted_connection.send_message(Messages.PUSH_EVENT_LOGS, data=json_data)
        if not response == Messages.SUCCESS_RESPONSE:
            raise Exception ("push_event_logs: Invalid response (%s)" % response)
        
        # Reconfigure the doors to get the latest timestamps
        self.configure_doors()

    def __str__(self): 
        return self.description
