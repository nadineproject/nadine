import sys
import hashlib
import random
import traceback
from datetime import datetime, timedelta, date

from django.test import SimpleTestCase
from django.conf import settings

from suds.client import Client


class UsaepayTestCase(SimpleTestCase):
    _client = None
    _token = None

    def get_client(self):
        if not self._client:
            url = settings.USA_EPAY_SOAP_1_4
            self._client = Client(url)
        return self._client

    def get_token(self, key, pin):
        if not self._token:
            # Hash our pin
            random.seed(datetime.now())
            salt = random.randint(0, sys.maxsize)
            salted_value = "%s%s%s" % (key, salt, pin)
            pin_hash = hashlib.sha1(salted_value.encode('utf-8'))

            client = self.get_client()
            self._token = client.factory.create('ueSecurityToken')
            self._token.SourceKey = key
            self._token.PinHash.Type = 'sha1'
            self._token.PinHash.Seed = salt
            self._token.PinHash.HashValue = pin_hash.hexdigest()
        return self._token

    def test_soap(self):
        if not hasattr(settings, 'USA_EPAY_SOAP_KEY'):
            return

        key = settings.USA_EPAY_SOAP_KEY
        pin = settings.USA_EPAY_SOAP_PIN

        client = self.get_client()
        token = self.get_token(key, pin)
        # TODO - This should not be hardcoded
        username = "jacob"
        cust_num = client.service.searchCustomerID(token, username);

        self.assertTrue(cust_num != None)
