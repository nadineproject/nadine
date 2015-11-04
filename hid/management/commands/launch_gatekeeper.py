import os
import time
import urllib
import sys
import requests
import json

from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from hid.models import Gatekeeper, Door, Messages

class GatekeeperConnection():
    
    def __init__(self):
        encryption_key = getattr(settings, 'HID_ENCRYPTION_KEY', None)
        if encryption_key is None:
            print "No encyrption key.  Use manage.py generate_key to create a new one"
            raise ImproperlyConfigured("Missing HID_ENCRYPTION_KEY setting")
        self.gatekeeper = Gatekeeper(encryption_key=encryption_key)
        
        self.keymaster_url = getattr(settings, 'HID_KEYMASTER_URL', None)
        if self.keymaster_url is None:
            raise ImproperlyConfigured("Missing HID_KEYMASTER_URL setting")

        self.doors = []

    def send_message(self, message):
        # Encrypt the message
        encrypted_message = self.gatekeeper.encrypt_message(message)
        
        # Send the message 
        response = requests.post(self.keymaster_url, data={'message':encrypted_message})
        
        # Process the response
        response_json = response.json()
        if 'error' in response_json:
            error = response_json['error']
            raise Exception(error)

        if 'message' in response_json:
            encrypted_return_message = response.json()['message']
            return self.gatekeeper.decrypt_message(encrypted_return_message)

        return None

    def process_configuration(self, configuration):
        config_json = json.loads(configuration)
        print "Configuration: %s" % config_json
        for d in config_json:
            door = Door(name=d['name'], ip_address=d['ip_address'], username=d['username'], password=d['password'])
            self.doors.append(door)

    def process_door_codes(self, response):
        print "Response: %s" % response


class Command(BaseCommand):
    help = "Launch the Gatekeeper"
    args = ""
    requires_system_checks = False

    def handle(self, *labels, **options):
        poll_delay = getattr(settings, 'HID_POLL_DELAY_SEC', 60)

        try:
            print "Starting up Gatekeeper..."
            connection = GatekeeperConnection()
            
            # Test the connection
            response = connection.send_message(Messages.TEST_QUESTION)
            if response == Messages.TEST_RESPONSE:
                print "Connection successfull!"
            else:
                raise Exception("Could not connect to Keymaster")

            # Pull the configuration
            print "Pulling door configuration..."
            response = connection.send_message(Messages.PULL_CONFIGURATION)
            connection.process_configuration(response)
            print "Configuring %d doors" % len(connection.doors)
            
            # Now loop and get new commands
            while True:
                response = connection.send_message(Messages.PULL_DOOR_CODES)
                connection.process_door_codes(response)
                response = connection.send_message(Messages.MARK_SUCCESS)
                if not response == Messages.SUCCESS_RESPONSE:
                    raise Exception("Did not receive proper success response!")
                time.sleep(poll_delay)
        except Exception as e:
            print "Error: %s" % str(e)
    
