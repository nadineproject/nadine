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

from hid import hid_control
from hid.hid_control import DoorController

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class Messages(object):
    TEST_QUESTION = "Are you the Keymaster?"
    TEST_RESPONSE = "Are you the Gatekeeper?"
    PULL_CONFIGURATION = "pull_configuration"
    PULL_DOOR_CODES = "pull_door_codes"
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
        elif incoming_message == Messages.MARK_SUCCESS:
            self.gatekeeper.mark_success()
            outgoing_message = Messages.SUCCESS_RESPONSE
        
        logger.debug("Outgoing Message: '%s' " % outgoing_message)
        return outgoing_message

    def pull_config(self):
        doors = []
        for d in Door.objects.filter(gatekeeper=self.gatekeeper):
            door = {'name':d.name, 'ip_address':d.ip_address, 'username':d.username, 'password':d.password}
            doors.append(door)
        return json.dumps(doors)

    def pull_door_codes(self):
        if self.gatekeeper.success_ts:
            new_codes = DoorCode.objects.filter(modified_ts__gt=self.gatekeeper.success_ts)
        else:
            new_codes = DoorCode.objects.all()
        if not new_codes:
            return "{}"
            
        codes = []
        for c in DoorCode.objects.all():
            u = c.user
            code = {'username':u.username, 'first_name': u.first_name, 'last_name':u.last_name, 'code':c.code}
            codes.append(code)
        return json.dumps(codes)


class GatekeeperManager(models.Manager):
    
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
    success_ts = models.DateTimeField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)

    def set_keymaster_url(self, keymaster_url):
        self.keymaster_url = keymaster_url

    def mark_success(self):
        self.success_ts = timezone.now()
        self.save()

    def get_encrypted_connection(self):
        if not 'keymaster_url' in self.__dict__:
            self.keymaster_url = None
        return EncryptedConnection(self.encryption_key, keymaster_url=self.keymaster_url)

    def process_configuration(self, configuration):
        self.doors = {}
        config_json = json.loads(configuration)
        logger.debug("Configuration: %s" % config_json)
        for d in config_json:
            name = d['name']
            door = Door(name=name, ip_address=d['ip_address'], username=d['username'], password=d['password'])
            self.doors[name] = door
            logger.info("Testing Door: %s" % name)
            controller = door.get_controller()
            controller.test_connection()
            controller.load_cardholders()

    def process_door_codes(self, response):
        logger.debug("process_door_codes: %s" % response)
        for code in response:
            pass

    def __str__(self): 
        return self.description


class Door(models.Model):
    name = models.CharField(max_length=16, unique=True)
    gatekeeper = models.ForeignKey(Gatekeeper)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    ip_address = models.GenericIPAddressField()

    def get_controller(self):
        if not 'controller' in self.__dict__:
            self.controller = DoorController(self.ip_address, self.username, self.password)
        return self.controller
    
    def __str__(self): 
        return "%s: %s" % (self.gatekeeper.description, self.name)


class DoorCode(models.Model):
    created_by = models.ForeignKey(User, related_name="+")
    modified_ts = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16, unique=True)

    def __str__(self): 
        return '%s - %s: %s' % (self.user, self.door, self.code)
