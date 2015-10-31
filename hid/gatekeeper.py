#!/usr/bin/env python

import os, sys, time, base64
import ssl, urllib, urllib2, requests

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured

from cryptography.fernet import Fernet

class GateKeeper:
    
    def __init__(self):
        self.encryption_key = getattr(settings, 'HID_ENCRYPTION_KEY', None)
        if self.encryption_key is None:
            raise ImproperlyConfigured("Missing HID_ENCRYPTION_KEY setting")

        self.keymaster_url = getattr(settings, 'HID_KEYMASTER_URL', None)
        if self.keymaster_url is None:
            raise ImproperlyConfigured("Missing HID_KEYMASTER_URL setting")

        self.poll_delay = getattr(settings, 'HID_POLL_DELAY_SEC', 60)

    def transmit_message(self, message):
        f = Fernet(self.encryption_key)
        encrypted_message = f.encrypt(message)
        return requests.post(self.keymaster_url, data={'message':encrypted_message})


if __name__ == "__main__":
    #from ... import nadine
    sys.path.insert(1, os.path.join(sys.path[0], '..'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nadine.settings")

    try:
        gatekeeper = GateKeeper()
        while True:
            message = "Hello World"
            response = gatekeeper.transmit_message(message)
            print response.text
            time.sleep(gatekeeper.poll_delay)
    except ImproperlyConfigured as e:
        print e
