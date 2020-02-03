import os
import abc
import json
import base64
import logging
import requests
import traceback
import threading
from datetime import datetime, time, date, timedelta

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    GET_TIME = "get_time"
    PULL_CONFIGURATION = "pull_configuration"
    CHECK_IN = "check_in"
    PULL_DOOR_CODES = "pull_door_codes"
    PUSH_EVENT_LOGS = "push_event_logs"
    NEW_DATA = "new_data"
    NO_NEW_DATA = "no_new_data"
    MARK_SUCCESS = "mark_success"
    MARK_SYNC = "mark_sync"
    LOG_MESSAGE = "log_message"
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
        if isinstance(encryption_key, str):
            encryption_key = bytes(encryption_key, encoding='utf-8')
        self.encryption_key = encryption_key
        self.farnet = Fernet(encryption_key)
        self.ttl = ttl
        self.keymaster_url = keymaster_url
        self.message = None
        self.data = None
        self.lock = threading.Lock()

    def decrypt_message(self, message):
        if isinstance(message, str):
            # Message must be bytes
            message = bytes(message, encoding='utf-8')
        # If you are getting a blank exception when this runs it might be because the encrypted message
        # was created in the future.  Check the time of the machine encrypting the message and try again --JLS
        decrypted_message = self.farnet.decrypt(message, ttl=self.ttl)
        return decrypted_message.decode(encoding='utf-8')

    def encrypt_message(self, message):
        if isinstance(message, str):
            # Message must be bytes
            message = bytes(message, encoding='utf-8')
        return self.farnet.encrypt(message)

    def send_message(self, message, data=None, encrypt=True):
        # Encrypt the message
        if encrypt:
            encrypted_message = self.encrypt_message(message)
            request_package = {'message':encrypted_message}
            if data:
                request_package['data'] = self.encrypt_message(data)
        else:
            request_package = {'text_message': message}
            if data:
                request_package['data'] = data

        # Send the message
        self.lock.acquire()
        try:
            response = requests.post(self.keymaster_url, data=request_package)
        finally:
            self.lock.release()
        if not response:
            logger.warn("Received blank response from Keymaster")
            return None

        # Process the response
        response_json = response.json()
        if 'error' in response_json:
            error = response_json['error']
            traceback.print_exc()
            raise Exception(error)

        if 'text_message' in response_json:
            return response_json['text_message']

        if 'message' in response_json:
            encrypted_return_message = response.json()['message']
            return self.decrypt_message(encrypted_return_message)

        return None

    def receive_message(self, request):
        # Encrypted message is in 'message' POST variable
        if not request.method == 'POST':
            raise Exception("Must be POST")
        if 'text_message' in request.POST:
            return request.POST['text_message']

        if not 'message' in request.POST:
            raise Exception("No message in POST")
        encrypted_message = request.POST['message']
        logger.debug("Received encrypted message.  Size: %d" % len(encrypted_message))

        try:
            self.message = self.decrypt_message(encrypted_message)
            logger.debug("Decrypted message: %s" % self.message)
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) == 0:
                # A blank error message is most likely at imestamp mismatch.
                # Check the times on the gatekeeper to make sure it's not in ahead of the keymaster
                raise Exception("Decryption error!  Possible keymaster/gatekeeper timestamp mismatch")
            else:
                raise Exception("Could not decrypt message! (%s)" % error_msg)

        # Encrypted data is in 'data' POST variable
        if 'data' in request.POST:
            encrypted_data = request.POST['data']
            decrypted_data = self.decrypt_message(encrypted_data)
            self.data = json.loads(decrypted_data)

        return self.message


class CardHolder(object):

    def __init__(self, id, first_name, last_name, username, code):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.code = code

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def is_same_person(self, cardholder):
        if cardholder.first_name == self.first_name:
            if cardholder.last_name == self.last_name:
                if cardholder.username == self.username:
                    return True
        return False

    def to_dict(self):
        me_dict = {'first_name':self.first_name, 'last_name':self.last_name, 'username':self.username}
        if self.id:
            me_dict['id'] = self.id
        if self.code:
            me_dict['code'] = self.code
        return me_dict

    def __repr__(self):
        id_str = ""
        if self.id:
            id_str = " (%s)" % self.id
        action_str = ""
        if hasattr(self, "action"):
            action_str = " (%s)" % self.action
        return "%s%s: %s%s" % (self.get_full_name(), id_str, self.code, action_str)

class DoorController(object):

    def __init__(self, name, ip_address, username, password):
        self.debug = False
        self.door_name = name
        self.door_ip = ip_address
        self.door_user = username
        self.door_pass = password
        self.clear_data()

    def door_url(self):
        # door_url = "https://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        door_url = "http://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        return door_url

    def cardholder_count(self):
        return len(self.cardholders_by_id)

    def clear_data(self):
        self.cardholders_by_id = {}
        self.cardholders_by_code = {}

    def save_cardholder(self, cardholder):
        if not cardholder.id in self.cardholders_by_id:
            self.cardholders_by_id[cardholder.id] = cardholder
        if cardholder.code and not cardholder.code in self.cardholders_by_code:
            self.cardholders_by_code[cardholder.code] = cardholder

    def get_cardholder_by_id(self, cardholderID):
        if cardholderID in self.cardholders_by_id:
            return self.cardholders_by_id[cardholderID]
        return None

    def get_cardholder_by_code(self, code):
        if code in self.cardholders_by_code:
            return self.cardholders_by_code[code]
        return None

    def process_door_codes(self, door_codes, load_credentials=True):
        logging.info("DoorController[%s]: Processing door codes (%d)" % (self.door_name, len(door_codes)))

        if load_credentials:
            self.load_credentials()

        changes = []
        for new_code in door_codes:
            first_name = new_code.get('first_name')
            last_name = new_code.get('last_name')
            username = new_code.get('username')
            code = new_code.get('code')
            new_cardholder = CardHolder(None, first_name, last_name, username, code)

            cardholder = self.get_cardholder_by_code(code)
            if cardholder:
                if new_cardholder.is_same_person(cardholder):
                    cardholder.action = 'no_change'
                else:
                    cardholder.action = 'delete'
                    changes.append(cardholder)
                    new_cardholder.action = 'add'
                    changes.append(new_cardholder)
            else:
                new_cardholder.action = 'add'
                changes.append(new_cardholder)

        # Now loop through all the cardholders and any that don't have an action
        # are in the controller but not in the given list.  Remove them.
        for cardholder in list(self.cardholders_by_id.values()):
            if not hasattr(cardholder, "action"):
                cardholder.action = 'delete'
                changes.append(cardholder)

        return changes

    def process_changes(self, change_list):
        for c in change_list:
            logging.debug("DoorController [%s]: %s - %s" % (self.door_name, c.action.title(), c.get_full_name()))
            if c.action == 'add':
                self.add_cardholder(c)
            elif c.action == 'delete':
                self.delete_cardholder(c)

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
    def add_cardholder(self, cardholder):
        """Add the given cardholder to the door."""

    @abc.abstractmethod
    def delete_cardholder(self, cardholder):
        """Delete the given cardholder from the door."""

    @abc.abstractmethod
    def pull_events(self, recordCount):
        """Pull the requested number of the most door events."""

    @abc.abstractmethod
    def is_locked(self):
        """Return True if the door is locked."""

    @abc.abstractmethod
    def lock_door(self):
        """Lock the door."""

    @abc.abstractmethod
    def unlock_door(self):
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

    def add_cardholder(self, cardholder):
        pass

    def delete_cardholder(self, cardholder):
        pass

    def pull_events(self, recordCount):
        return []

    def is_locked(self):
        return True

    def lock_door(self):
        pass

    def unlock_door(self):
        pass


class Gatekeeper(object):
    def __init__(self, config):
        if not 'KEYMASTER_URL' in config:
            raise Exception("No KEYMASTER_URL in configuration")
        if not 'KEYMASTER_SECRET' in config:
            raise Exception("No KEYMASTER_SECRETin configuration")

        self.encrypted_connection = EncryptedConnection(config['KEYMASTER_SECRET'], config['KEYMASTER_URL'])
        self.card_secret = config.get('CARD_SECRET', None)
        self.event_count = config.get('EVENT_SYNC_COUNT', 100)
        self.lock_key_code = config.get('LOCK_KEY', None)
        self.unlock_key_code = config.get('UNLOCK_KEY', None)
        self.debug = config.get('DEBUG', False)

    def get_connection(self):
        return self.encrypted_connection

    def test_keymaster_connection(self):
        response = self.encrypted_connection.send_message(Messages.TEST_QUESTION)
        if not response == Messages.TEST_RESPONSE:
            raise Exception("Could not connect to Keymaster")

    def configure_doors(self):
        logging.info("Gatekeeper: Pulling door configuration...")
        self.doors = {}
        configuration = self.encrypted_connection.send_message(Messages.PULL_CONFIGURATION)
        config_json = json.loads(configuration)

        for door_info in config_json:
            name = door_info.get('name')
            door_type= door_info.get('door_type')
            ip_address=door_info.get('ip_address')
            username=door_info.get('username')
            password=door_info.get('password')
            logging.debug("Gatekeeper: %s = %s|%s|%s" % (name, door_type, ip_address, username))

            # Find our controller for this door
            if door_type == DoorTypes.HID:
                from hid_control import HIDDoorController
                controller = HIDDoorController(name, ip_address, username, password)
                controller.debug = self.debug
            elif door_type == DoorTypes.TEST:
                controller = TestDoorController(name, ip_address, username, password)
            else:
                raise NotImplementedError
            door_info['controller'] = controller

            logging.debug("Gatekeeper: Loading credentials for '%s'" % name)
            controller.load_credentials()
            logging.debug("Gatekeeper: Number of cardholders = %d" % len(controller.cardholders_by_id))

            self.doors[name] = door_info

    def get_doors(self):
        if not 'doors' in self.__dict__:
            raise Exception("Doors not configured")
        return self.doors

    def get_door(self, door_name):
        if door_name not in self.get_doors():
            raise Exception("Door not found")
        return self.doors[door_name]

    def set_system_clock(self):
        # For this to work the user running the gatekeepr app must have sudo access
        # for the date command with password turned off.  If this is not set, it will
        # fail silently without doing anything. --JLS
        logging.info("Gatekeeper: Pulling the time from the keymaster...")
        try:
            km_time = self.encrypted_connection.send_message(Messages.GET_TIME, encrypt=False)
            logging.debug("Gatekeeper: Received: %s" % km_time)
            date_cmd = 'echo "" | sudo -kS date -s "%s" > /dev/null 2> /dev/null' % km_time
            os.system(date_cmd)
            return True
        except Exception as e:
            logging.info("Gatekeeper: Failed to set system clock! (%s)" % e)
        return False

    def sync_clocks(self):
        logging.info("Gatekeeper: Syncing the door clocks...")
        for door in list(self.get_doors().values()):
            controller = door['controller']
            controller.set_time()

    def load_data(self):
        for door in list(self.get_doors().values()):
            controller = door['controller']
            controller.load_credentials()

    def clear_all_codes(self):
        logging.info("Gatekeeper: Clearing all door codes...")
        for door in list(self.get_doors().values()):
            controller = door['controller']
            controller.clear_door_codes()

    def pull_door_codes(self):
        logging.info("Gatekeeper: Pulling door codes from the keymaster...")
        response = self.encrypted_connection.send_message(Messages.PULL_DOOR_CODES)
        door_codes = json.loads(response)

        # Inject our magic keys in to the list of door codes
        if self.lock_key_code:
            door_codes.append({'first_name':'Lock', 'last_name':'Key', 'username':'lockkey', 'code':self.lock_key_code})
        if self.unlock_key_code:
            door_codes.append({'first_name':'Unlock', 'last_name':'Key', 'username':'unlockkey', 'code':self.unlock_key_code})

        # Decode the doors coming from the keymaster if we have a card secret
        if self.card_secret:
            for c in door_codes:
                c['code'] = self.decode_door_code(c['code'])

        for door in list(self.get_doors().values()):
            controller = door['controller']
            changes = controller.process_door_codes(door_codes)
            controller.process_changes(changes)

    def pull_event_logs(self, record_count=-1):
        logging.debug("Gatekeeper: Pulling event logs from the doors...")
        if record_count <= 0:
            record_count = self.event_count
        event_logs = {}
        for door_name, door in list(self.get_doors().items()):
            logging.debug("Gatekeeper: Pulling %d logs from '%s'" % (record_count, door_name))
            controller = door['controller']
            door_events = controller.pull_events(record_count)
            if self.card_secret:
                for e in door_events:
                    if 'cardNumber' in e:
                        # e['cardNumber'] = self.encode_door_code(e['cardNumber']).decode('utf-8')
                        e['cardNumber'] = self.encode_door_code(e['cardNumber'])
            event_logs[door_name] = door_events
        return event_logs

    def push_event_logs(self, event_logs, reconfig=True):
        logging.info("Gatekeeper: Pushing event logs to keymaster...")
        json_data = json.dumps(event_logs)
        response = self.encrypted_connection.send_message(Messages.PUSH_EVENT_LOGS, data=json_data)
        if not response == Messages.SUCCESS_RESPONSE:
            raise Exception ("push_event_logs: Invalid response (%s)" % response)

        # Reconfigure the doors to get the latest timestamps
        if reconfig:
            self.configure_doors()

    def send_gatekeper_log(self, log_text):
        logging.info("Gatekeeper: Sending gatekeeper log to keymaster...")
        json_data = json.dumps({'log_text':log_text})
        response = self.encrypted_connection.send_message(Messages.LOG_MESSAGE, data=json_data)
        if not response == Messages.SUCCESS_RESPONSE:
            raise Exception ("send_gatekeper_log: Invalid response (%s)" % response)

    def magic_key_test(self, door_name, code):
        logging.debug("Gatekeeper: Magic key test...")
        if code:
            door = self.get_door(door_name)
            controller = door['controller']
            if code == self.unlock_key_code:
                logging.info("Gatekeeper: Unlocking door")
                controller.unlock_door()
            elif code == self.lock_key_code:
                logging.info("Gatekeeper: Locking door")
                controller.lock_door()

    def toggle_door(self, door_name):
        logging.info("Gatekeeper: Toggle Door!")
        door = self.get_door(door_name)
        controller = door['controller']
        if controller.is_locked():
            logging.info("Gatekeeper: Unlocking door")
            controller.unlock_door()
        else:
            logging.info("Gatekeeper: Locking door")
            controller.lock_door()

    def encode_door_code(self, clear):
        if not clear: return None
        # TODO - Bypassing local card encryption -- JLS
        # enc = []
        # for i in range(len(clear)):
        #     key_c = self.card_secret[i % len(self.card_secret)]
        #     if isinstance(key_c, int): key_c = chr(key_c)
        #     enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        #     enc.append(enc_c)
        # new_enc =  base64.urlsafe_b64encode("".join(enc).encode()).decode()
        # return new_enc[::-1][2:]
        return clear

    def decode_door_code(self, enc):
        if not enc: return None
        # TODO - Bypassing local card encryption -- JLS
        # dec = []
        # enc = base64.urlsafe_b64decode(enc[::-1] + '==').decode()
        # for i in range(len(enc)):
        #     key_c = self.card_secret[i % len(self.card_secret)]
        #     if isinstance(key_c, int): key_c = chr(key_c)
        #     dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        #     dec.append(dec_c)
        # return "".join(dec)
        return enc

    def __str__(self):
        return self.description


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
