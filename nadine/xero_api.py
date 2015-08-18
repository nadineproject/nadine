from xero import Xero
from xero.auth import PrivateCredentials

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

import pytz
from datetime import datetime, time, date, timedelta
from xml.dom.minidom import parse, parseString

from nadine.models.core import XeroContact

XERO_ERROR_MESSAGES = {
    'no_key': 'Please set your XERO_CONSUMER_KEY setting.',
    'no_secret': 'Please set your XERO_PRIVATE_KEY setting. Must be a path to your privatekey.pem',
}

def test_xero_connection():
    api = XeroAPI()
    try:
        api = XeroAPI()
        api.xero.contacts.filter(Name='John Smith')
        return True
    except ImproperlyConfigured as ice:
        raise ice
    except Exception as e:
        pass
    return False

class XeroAPI:
    
    def __init__(self):
        consumer_key = getattr(settings, 'XERO_CONSUMER_KEY', None)
        if consumer_key is None:
            raise ImproperlyConfigured(XERO_ERROR_MESSAGES['no_key'])

        private_key = getattr(settings, 'XERO_PRIVATE_KEY', None)
        if private_key is None:
            raise ImproperlyConfigured(XERO_ERROR_MESSAGES['no_secret'])

        with open(private_key) as keyfile:
            rsa_key = keyfile.read()

        self.credentials = PrivateCredentials(consumer_key, rsa_key)
        self.xero = Xero(self.credentials)

    def get_all_contacts(self):
        return self.xero.contacts.all()

    def find_contacts(self, user):
        return self.xero.contacts.filter(Name__contains=user.last_name)

    def get_contact(self, user):
        xero_contact = XeroContact.objects.filter(user=user).first()
        if xero_contact:
            search = self.xero.contacts.get(xero_contact.xero_id)
            if search and len(search) == 1:
                return search[0]
        return None

    def save_contact(self, contact_data):
        print contact_data
        contact_id = None
        try:
            result = self.xero.contacts.save(contact_data)
            if len(result) == 1:
                contact_id = result[0]['ContactID']
        except Exception as e:
            raise Exception("Xero Contact Save Failed", e)
        return contact_id

    def add_contact(self, contact_data):
        print contact_data
        contact_id = None
        try:
            result = self.xero.contacts.put(contact_data)
            print result
            if len(result) == 1:
                contact_id = result[0]['ContactID']
        except Exception as e:
            raise Exception("Xero Contact Save Failed", e)
        return contact_id

    def save_or_put_contact(self, contact_data):
        print contact_data
        contact_id = None
        try:
            result = self.xero.contacts.save_or_put(contact_data)
            print result
            xml = result[3]['xml']
            dom = parseString(xml)
            id_elm = dom.getElementsByTagName('ContactID')
            if id_elm and len(id_elm) > 0:
                contact_id = id_elm[0].firstChild.nodeValue
        except Exception as e:
            raise Exception("Xero Contact Save Failed", e)
        return contact_id

    def sync_user_data(self, user):
        xero_contact = XeroContact.objects.filter(user=user).first()
        
        contact_data = {}
        contact_data['Name'] = user.get_full_name()
        contact_data['FirstName'] = user.first_name
        contact_data['LastName'] = user.last_name
        contact_data['EmailAddress'] = user.email
        contact_data['AccountNumber'] = user.username
        if xero_contact:
            contact_data['ContactID'] = xero_contact.xero_id
            xero_id = self.save_contact(contact_data)
        else:
            xero_id = self.add_contact(contact_data)
            xero_contact = XeroContact.objects.create(user=user, xero_id=xero_id)
            
        # Update the sync timestamp
        xero_contact.last_sync = timezone.now()
        xero_contact.save()

    def get_invoices(self, user):
        xero_contact = XeroContact.objects.filter(user=user).first()
        if not xero_contact:
            return None
        return self.xero.invoices.filter(Contact_ContactID=xero_contact.xero_id)

    def get_repeating_invoices(self, user):
        xero_data = None
        xero_contact = XeroContact.objects.filter(user=user).first()
        if xero_contact:
            xero_data = self.xero.repeatinginvoices.filter(Contact_ContactID=xero_contact.xero_id)
            if xero_data:
                for invoice in xero_data:
                    nsd = invoice['Schedule']['NextScheduledDate']
                    # Example: '1440417600000+1200' = 08/25/2015 tz=Pacific/LA
                    unix_time = int(nsd[6:len(nsd)-10])
                    # The UTC offset comes in with the date but I'm not sure how to convert that
                    # We know it's coming in NZ time -- JLS
                    dt = datetime.fromtimestamp(unix_time)
                    tz = pytz.timezone("Pacific/Auckland")
                    tz_dt = tz.localize(dt)
                    local_dt = timezone.localtime(tz_dt)
                    # Fuck it!  I'm just adding a day
                    invoice['NextScheduledDate'] = dt + timedelta(days=1)
            #print xero_data
        return xero_data

    def create_invoice(self):
        # Clearly just a test -- JLS
        xero = self.xero
        invoice = {
                    u'Status': u'DRAFT',
                    u'Total': u'264.00',
                    u'CurrencyRate': u'1.000000',
                    u'Reference': u'sdfghsfgh',
                    u'Type': u'ACCREC',
                    u'CurrencyCode': u'AUD',
                    u'AmountPaid': u'0.00',
                    u'TotalTax': u'24.00',
                    u'Contact': {
                        u'Name': u'Test One'
                    },
                    u'AmountDue': u'264.00',
                    u'Date': datetime.date(2014, 7, 24),
                    u'LineAmountTypes': u'Exclusive',
                    u'LineItems': {
                        u'LineItem': {
                            u'AccountCode': u'200',
                            u'TaxAmount': u'24.00',
                            u'Description': u'fgshfsdh',
                            u'UnitAmount': u'24.00',
                            u'TaxType': u'OUTPUT',
                            u'ItemCode': u'sfghfshg',
                            u'LineAmount': u'240.00',
                            u'Quantity': u'10.0000'
                        }
                    },
                    u'SubTotal': u'240.00',
                    u'DueDate': datetime.date(2014, 7, 24)
                }
        #xero.invoices.put(invoice)