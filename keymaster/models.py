import json
import logging
import requests

from datetime import datetime, time, date, timedelta

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.utils import timezone

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


class Keymaster(object):
    def __init__(self, gatekeeper):
        self.gatekeeper = gatekeeper
        self.encrypted_connection = self.gatekeeper.get_encrypted_connection()

    def process_message(self, incoming_message):
        logger.debug("Incoming Message: '%s' " % incoming_message)
        
        outgoing_message = "No message"
        if incoming_message == Messages.TEST_QUESTION:
            outgoing_message = Messages.TEST_RESPONSE
        elif incoming_message == Messages.PULL_CONFIGURATION:
            outgoing_message = self.pull_config()
        elif incoming_message == Messages.PULL_DOOR_CODES:
            outgoing_message = self.pull_door_codes()
        elif incoming_message == Messages.FORCE_SYNC:
            outgoing_message = self.pull_door_codes(forceSync=True)
        elif incoming_message == Messages.MARK_SUCCESS:
            self.gatekeeper.mark_success()
            outgoing_message = Messages.SUCCESS_RESPONSE
        
        logger.debug("Outgoing Message: '%s' " % outgoing_message)
        return outgoing_message

    def pull_config(self):
        doors = []
        for d in Door.objects.filter(gatekeeper=self.gatekeeper):
            door = {'name':d.name, 'door_type':d.door_type, 'ip_address':d.ip_address, 'username':d.username, 'password':d.password}
            doors.append(door)
        return json.dumps(doors)

    def pull_door_codes(self, forceSync=False):
        if not forceSync:
            if self.gatekeeper.sync_ts:
                if DoorCode.objects.filter(modified_ts__gt=self.gatekeeper.sync_ts).count() == 0:
                    # Nothing to do here
                    return []
        # Pull all the codes and send them back
        codes = []
        for c in DoorCode.objects.all():
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)


class GatekeeperManager(models.Manager):
    
    # Pull an object from the database linked by the incoming IP address
    def by_ip(self, ip):
        try:
            gatekeeper = self.get(ip_address=ip)
            if not gatekeeper.is_enabled:
                raise Exception("Gatekeeper for this IP address is disabled")
            # A save updates the access_ts
            gatekeeper.save()
            return gatekeeper
        except MultipleObjectsReturned as me:
            logger.error("Multiple Gatekeepers returned for IP: %s" % ip)
        except ObjectDoesNotExist as de:
            # The first time we see a message from a given IP we create a disabled gatekeeper
            self.create(ip_address=ip, description="New Gatekeeper", is_enabled=False)
            
        return None
    
    # Create an instance from values in our system settings file
    def from_settings(self):
        encryption_key = getattr(settings, 'HID_ENCRYPTION_KEY', None)
        if encryption_key is None:
            print "No encyrption key.  Use manage.py generate_key to create a new one"
            raise ImproperlyConfigured("Missing HID_ENCRYPTION_KEY setting")
        
        keymaster_url = getattr(settings, 'HID_KEYMASTER_URL', None)
        if keymaster_url is None:
            raise ImproperlyConfigured("Missing HID_KEYMASTER_URL setting")
        
        gk = Gatekeeper(encryption_key=encryption_key)
        gk.set_keymaster_url(keymaster_url)
        return gk


class Gatekeeper(models.Model):
    objects = GatekeeperManager()
    
    description = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(blank=False, null=False, unique=True)
    encryption_key = models.CharField(max_length=128)
    access_ts = models.DateTimeField(auto_now=True)
    sync_ts = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)

    def set_keymaster_url(self, keymaster_url):
        self.keymaster_url = keymaster_url

    def mark_success(self):
        self.sync_ts = timezone.now()
        self.save()

    def force_sync(self):
        self.sync_ts = None
        self.save()

    def get_encrypted_connection(self):
        if not 'keymaster_url' in self.__dict__:
            self.keymaster_url = None
        return EncryptedConnection(self.encryption_key, keymaster_url=self.keymaster_url)

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


class DoorTypes(object):
    HID = "hid"
    MAYPI = "maypi"
    
    CHOICES = (
        (HID, "Hid Controller"),
        (MAYPI, "Maypi Controller"),
    )

class Door(models.Model):
    name = models.CharField(max_length=16, unique=True)
    door_type = models.CharField(max_length=16, choices=DoorTypes.CHOICES)
    gatekeeper = models.ForeignKey(Gatekeeper)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    ip_address = models.GenericIPAddressField()

    def get_controller(self):
        if not 'controller' in self.__dict__:
            if self.door_type == DoorTypes.HID:
                self.controller = DoorController(self.ip_address, self.username, self.password)
            elif self.door_type == DoorTypes.MAYPI:
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
    
    def __str__(self): 
        return "%s: %s" % (self.gatekeeper.description, self.name)


class DoorCode(models.Model):
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True)

    def __str__(self): 
        return '%s: %s' % (self.user, self.code)

class DoorEventTypes(object):
    UNKNOWN = "0"
    UNRECOGNIZED = "1"
    GRANTED = "2"
    DENIED = "3"
    LOCKED = "4"
    UNLOCKED = "5"
    
    CHOICES = (
        (UNKNOWN, 'Unknown'),
        (UNRECOGNIZED, 'Unrecognized Card'),
        (GRANTED, 'Access Granted'),
        (GRANTED, 'Access Denied'),
        (LOCKED, 'Door Locked'),
        (UNLOCKED, 'Door Unlocked'),
    )

class DoorLog(models.Model):
    timestamp = models.DateTimeField(null=False)
    door = models.ForeignKey(Door, null=False)
    user = models.ForeignKey(User, null=True, db_index=True)
    code = models.CharField(max_length=16)
    event_type = models.CharField(max_length=1, choices=DoorEventTypes.CHOICES, default=DoorEventTypes.UNKNOWN, null=False)
    event_description = models.CharField(max_length=256)
    