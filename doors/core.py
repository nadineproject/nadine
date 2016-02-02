import abc
import json
import base64
import logging
import requests
import traceback
from datetime import datetime, time, date, timedelta

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    PULL_CONFIGURATION = "pull_configuration"
    CHECK_IN = "check_in"
    PULL_DOOR_CODES = "pull_door_codes"
    PUSH_EVENT_LOGS = "push_event_logs"
    NEW_DATA = "new_data"
    NO_NEW_DATA = "no_new_data"
    MARK_SUCCESS = "mark_success"
    MARK_SYNC = "mark_sync"
    SUCCESS_RESPONSE = "OK"


class DoorTypes(object):
    HID = "hid"
    MAYPI = "maypi"
    TEST = "test"
    
    CHOICES = (
        (HID, "Hid Controller"),
        (MAYPI, "Maypi Controller"),
        (TEST, "Test Controller"),
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
        # If you are getting a blank exception when this runs it might be because the encrypted message
        # was created in the future.  Check the time of the machine encrypting the message and try again --JLS
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
        # Encrypted message is in 'message' POST variable
        if not request.method == 'POST':
            raise Exception("Must be POST")
        if not 'message' in request.POST:
            raise Exception("No message in POST")
        encrypted_message = request.POST['message']
        logger.debug("Received encrypted message.  Size: %d" % len(encrypted_message))
        
        try:
            self.message = self.decrypt_message(encrypted_message)
            logger.debug("Decrypted message: %s" % self.message)
        except Exception as e:
            raise Exception("Could not decrypt message! (%s)" % str(e))
        
        # Encrypted data is in 'data' POST variable
        if 'data' in request.POST:
            encrypted_data = request.POST['data']
            decrypted_data = self.decrypt_message(encrypted_data)
            self.data = json.loads(decrypted_data)
        
        return self.message


class DoorController(object):
     
    def __init__(self, ip_address, username, password):
        self.door_ip = ip_address
        self.door_user = username
        self.door_pass = password
        self.clear_data()

    def door_url(self):
        door_url = "https://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        return door_url

    def cardholder_count(self):
        return len(self.cardholders_by_username)

    def clear_data(self):
        self.cardholders_by_id = {}
        self.cardholders_by_username = {}

    def save_cardholder(self, cardholder):
        if 'cardholderID' in cardholder:
            self.cardholders_by_id[cardholder.get('cardholderID')] = cardholder
        if 'username' in cardholder:
            self.cardholders_by_username[cardholder.get('username')] = cardholder

    def get_cardholder_by_id(self, cardholderID):
        if cardholderID in self.cardholders_by_id:
            return self.cardholders_by_id[cardholderID]
        return None

    def get_cardholder_by_username(self, username):
        if username in self.cardholders_by_username:
            return self.cardholders_by_username[username]
        return None

    def process_door_codes(self, door_codes, load_credentials=True):
        if load_credentials:
            self.load_credentials()

        changes = []
        for new_code in door_codes:
            username = new_code.get('username')
            cardholder = self.get_cardholder_by_username(username)
            #print "username: %s, cardholder: %s" % (username, cardholder)
            if cardholder:
                card_number = cardholder.get('cardNumber')
                if card_number and card_number != new_code.get('code'):
                    cardholder['action'] = 'change'
                    cardholder['new_code'] = new_code['code']
                    changes.append(cardholder)
                else:
                    cardholder['action'] = 'no_change'
            else:
                new_cardholder = {'action':'add', 'username':username}
                new_cardholder['forname'] = new_code.get('first_name')
                new_cardholder['surname'] = new_code.get('last_name')
                new_cardholder['full_name'] = "%s %s" % (new_code.get('first_name'), new_code.get('last_name'))
                new_cardholder['new_code'] = new_code.get('code')
                changes.append(new_cardholder)
        
        # Now loop through all the cardholders and any that don't have an action
        # are in the controller but not in the given list.  Remove them.
        for cardholder in self.cardholders_by_id.values():
            if not 'action' in cardholder:
                cardholder['action'] = 'delete'
                changes.append(cardholder)
        
        return changes
    
    ################################################################################
    # Abstract Methods
    ################################################################################
    
    @abc.abstractmethod
    def test_connection(self):
       """Tests the connection with the door."""
    
    @abc.abstractmethod
    def set_time(self):
        """Set the door time."""
    
    @abc.abstractmethod
    def load_cardholders(self):
        """Load the cardholder data from the door."""
    
    @abc.abstractmethod
    def load_credentials(self):
        """Load the credential data from the door."""
    
    @abc.abstractmethod
    def clear_door_codes(self):
        """Clear all data from the door."""
    
    @abc.abstractmethod
    def process_changes(self, change_list):
        """Process the changes at the door."""

    @abc.abstractmethod
    def pull_events(self, recordCount):
        """Pull the requested number of the most door events."""

    @abc.abstractmethod
    def is_locked(self):
        """Return True if the door is locked."""

    @abc.abstractmethod
    def lock(self):
        """Lock the door."""

    @abc.abstractmethod
    def unlock(self):
        """Unlock the door."""


class TestDoorController(DoorController):

    def test_connection(self):
       return True
    
    def load_cardholders(self):
        pass
    
    def set_time(self):
        pass
    
    def load_credentials(self):
        pass
    
    def clear_door_codes(self):
        pass
    
    def process_changes(self, change_list):
        pass
    
    def pull_events(self, recordCount):
        return []
    
    def is_locked(self):
        return True
    
    def lock(self):
        pass
    
    def unlock(self):
        pass


class Gatekeeper(object):
    def __init__(self, config):
        self.encrypted_connection = EncryptedConnection(config['KEYMASTER_SECRET'], config['KEYMASTER_URL'])
        self.card_secret = config.get('CARD_SECRET', None)
        self.event_count = config.get('EVENT_SYNC_COUNT', 100)
        self.magic_key_code = config.get('MAGIC_KEY', None)
    
    def get_connection(self):
        return self.encrypted_connection
    
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
        for door_info in config_json:
            name = door_info.get('name')
            door_type= door_info.get('door_type')
            ip_address=door_info.get('ip_address')
            username=door_info.get('username')
            password=door_info.get('password')
            
            # Find our controller for this door
            if door_type == DoorTypes.HID:
                from hid_control import HIDDoorController
                controller = HIDDoorController(ip_address, username, password)
            elif door_type == DoorTypes.TEST:
                controller = TestDoorController(ip_address, username, password)
            else:
                raise NotImplementedError
            door_info['controller'] = controller

            logger.debug("Gatekeeper: Loading credentials for '%s'" % name)
            controller.load_credentials()
            self.doors[name] = door_info
    
    def get_doors(self):
        if not 'doors' in self.__dict__:
            raise Exception("Doors not configured")
        return self.doors
    
    def get_door(self, door_name):
        if door_name not in self.get_doors():
            raise Exception("Door not found")
        return self.doors[door_name]
    
    def sync_clocks(self):
        print "Gatekeeper: Syncing the door clocks..."
        for door in self.get_doors().values():
            controller = door['controller']
            controller.set_time()
    
    def load_data(self):
        for door in self.get_doors().values():
            controller = door['controller']
            controller.load_credentials()
    
    def clear_all_codes(self):
        print "Gatekeeper: Clearing all door codes..."
        for door in self.get_doors().values():
            controller = door['controller']
            door.clear_door_codes()
    
    def pull_door_codes(self):
        print "Gatekeeper: Pulling door codes from the keymaster..."
        response = self.encrypted_connection.send_message(Messages.PULL_DOOR_CODES)
        doorcode_json = json.loads(response)
        logger.debug(doorcode_json)
        for door in self.get_doors().values():
            controller = door['controller']
            changes = controller.process_door_codes(doorcode_json)
            logger.debug("Changes: %s: " % changes)
            controller.process_changes(changes)
    
    def pull_event_logs(self, record_count=-1):
        print "Gatekeeper: Pulling event logs from the doors..."
        if record_count <= 0:
            record_count = self.event_count
        event_logs = {}
        for door_name, door in self.get_doors().items():
            print "Gatekeeper: Pulling %d logs from '%s'" % (record_count, door_name)
            controller = door['controller']
            door_logs = controller.pull_events(record_count)
            event_logs[door_name] = door_logs
        return event_logs
    
    def push_event_logs(self, record_count=-1):
        print "Gatekeeper: Pushing event logs to keymaster..."
        if record_count <= 0:
            record_count = self.event_count
        event_logs = self.pull_event_logs(record_count)
        json_data = json.dumps(event_logs)
        response = self.encrypted_connection.send_message(Messages.PUSH_EVENT_LOGS, data=json_data)
        if not response == Messages.SUCCESS_RESPONSE:
            raise Exception ("push_event_logs: Invalid response (%s)" % response)
        
        # Reconfigure the doors to get the latest timestamps
        self.configure_doors()
    
    def magic_key(self, door_name):
        door = self.get_door(door_name)
        controller = door['controller']
        if controller.is_locked():
            controller.unlock()
        else:
            controller.lock()
    
    def encode_door_code(self, clear):
        enc = []
        for i in range(len(clear)):
            key_c = self.card_secret[i % len(self.card_secret)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        e = base64.urlsafe_b64encode("".join(enc))
        return e[::-1][1:]

    def decode_door_code(self, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc[::-1] + "=")
        for i in range(len(enc)):
            key_c = self.card_secret[i % len(self.card_secret)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)
    
    def __str__(self): 
        return self.description
