import sys
import hashlib
import random
from datetime import datetime, timedelta

from django.conf import settings

from suds.client import Client

class EPayAPI_SOAP:

    def __init__(self):
        url = settings.USA_EPAY_URL2
        key = settings.USA_EPAY_KEY2
        pin = settings.USA_EPAY_PIN2

        self.client = Client(url)

        # Hash our pin
        random.seed(datetime.now())
        seed = random.randint(0, sys.maxint)
        pin_hash = hashlib.sha1("%s%s%s" % (key, seed, pin))

        self.token = self.client.factory.create('ueSecurityToken')
        self.token.SourceKey = key
        self.token.PinHash.Type = 'sha1'
        self.token.PinHash.Seed = seed
        self.token.PinHash.HashValue = pin_hash.hexdigest()


    def getCustomerNumber(self, username):
        return self.client.service.searchCustomerID(self.token, username);

    def getAllCustomers(self, username):
        return None
