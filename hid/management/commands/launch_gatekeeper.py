import os
import time
import urllib
import sys
import requests

from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from hid.models import Gatekeeper

class Command(BaseCommand):
    help = "Launch the Gatekeeper"
    args = ""
    requires_system_checks = True

    def handle(self, *labels, **options):
        poll_delay = getattr(settings, 'HID_POLL_DELAY_SEC', 60)
        keymaster_url = getattr(settings, 'HID_KEYMASTER_URL', None)
        if keymaster_url is None:
            raise ImproperlyConfigured("Missing HID_KEYMASTER_URL setting")
        encryption_key = getattr(settings, 'HID_ENCRYPTION_KEY', None)
        if encryption_key is None:
            print "Example Key: %s" % Fernet.generate_key()
            raise ImproperlyConfigured("Missing HID_ENCRYPTION_KEY setting")
    
        gatekeeper = Gatekeeper(encryption_key=encryption_key)

        try:
            print "Starting up Gatekeeper..."
            while True:
                message = "Are you the Keymaster?"
                encrypted_message = gatekeeper.encrypt_message(message)
                response = requests.post(keymaster_url, data={'message':encrypted_message})
                #print "%s: response = %s" %(datetime.now(), response.text)
                response_json = response.json()
                if 'error' in response_json:
                    print "Error: %s" % response_json['error']
                if 'message' in response_json:
                    encrypted_return_message = response.json()['message']
                    return_message = gatekeeper.decrypt_message(encrypted_return_message)
                    print "Response: %s" % return_message
                time.sleep(poll_delay)
        except ImproperlyConfigured as e:
            print "Error: %s" % str(e)