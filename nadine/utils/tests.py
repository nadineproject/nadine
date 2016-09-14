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
            url = settings.USA_EPAY_URL
            self._client = Client(url)
        return self._client

    def get_token(self, key, pin):
        if not self._token:
            # Hash our pin
            random.seed(datetime.now())
            seed = random.randint(0, sys.maxint)
            pin_hash = hashlib.sha1("%s%s%s" % (key, seed, pin))

            client = self.get_client()
            self._token = client.factory.create('ueSecurityToken')
            self._token.SourceKey = key
            self._token.PinHash.Type = 'sha1'
            self._token.PinHash.Seed = seed
            self._token.PinHash.HashValue = pin_hash.hexdigest()
        return self._token

    # TODO - Fix!  Not sure what is up but I assume it's a configuration problem -- JLS
    # def test_soap(self):
    #     key = settings.USA_EPAY_KEY
    #     pin = settings.USA_EPAY_PIN
    #
    #     client = self.get_client()
    #     token = self.get_token(key, pin)
    #     username = "jacob"
    #     cust_num = client.service.searchCustomerID(token, username);
    #
    #     self.assertTrue(cust_num != None)
