import sys
import hashlib
import random
import traceback
from datetime import datetime, timedelta, date

from django.test import SimpleTestCase
from django.conf import settings

from suds.client import Client
import mailgun

class MailgunTestCase(SimpleTestCase):
    bob_email = "bob@bob.net"
    bob = "Bob Smith <%s>" % bob_email
    alice_email = "alice@312main.ca"
    alice = "Alice Smith <%s>" % alice_email
    frank_email = "frank@example.com"
    frank = "Frank Smith <%s>" % frank_email
    mailgun_data = {'from':bob,
        'subject': "This is a test",
        'to':[alice, frank, bob],
        'cc':[frank, alice, bob],
        'bcc':[bob, alice, frank],
    }

    def test_address_map(self):
        addresses = mailgun.address_map(self.mailgun_data, 'BUNK', [])
        self.assertEquals(addresses, {})

        exclude = []
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 3)
        self.assertEqual(self.alice_email, addresses.keys()[0], exclude)
        self.assertEqual(self.bob_email, addresses.keys()[2], exclude)

        exclude = [self.bob_email]
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 2)
        self.assertEqual(self.alice_email, addresses.keys()[0], exclude)

    def test_clean_mailgun_data(self):
        clean_data = mailgun.clean_mailgun_data(self.mailgun_data)
        # print clean_data
        tos = clean_data['to']
        self.assertEqual(len(tos), 1)
        self.assertEqual(tos[0], self.alice)
        ccs = clean_data['cc']
        self.assertEqual(len(ccs), 0)
        bccs = clean_data['bcc']
        self.assertEqual(len(bccs), 1)
        self.assertEqual(bccs[0], self.frank)


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
            seed = random.randint(0, sys.maxsize)
            pin_hash = hashlib.sha1("%s%s%s" % (key, seed, pin))

            client = self.get_client()
            self._token = client.factory.create('ueSecurityToken')
            self._token.SourceKey = key
            self._token.PinHash.Type = 'sha1'
            self._token.PinHash.Seed = seed
            self._token.PinHash.HashValue = pin_hash.hexdigest()
        return self._token

    def test_soap(self):
        if not hasattr(settings, 'USA_EPAY_KEY'):
            return

        key = settings.USA_EPAY_KEY
        pin = settings.USA_EPAY_PIN

        client = self.get_client()
        token = self.get_token(key, pin)
        username = "jacob"
        cust_num = client.service.searchCustomerID(token, username);

        self.assertTrue(cust_num != None)
