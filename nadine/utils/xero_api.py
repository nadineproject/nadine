from datetime import datetime

from xero import Xero
from xero.auth import PrivateCredentials

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

import pytz
from datetime import datetime, time, date, timedelta
from xml.dom.minidom import parse, parseString

from nadine.models.profile import XeroContact

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
        self.deposit_account = getattr(settings, 'XERO_DEPOSIT_ACCOUNT', None)
        if self.deposit_account is None:
            raise ImproperlyConfigured("Please set your XERO_DEPOSIT_ACCOUNT setting.")

        consumer_key = getattr(settings, 'XERO_CONSUMER_KEY', None)
        if consumer_key is None:
            raise ImproperlyConfigured("Please set your XERO_CONSUMER_KEY setting.")

        private_key = getattr(settings, 'XERO_PRIVATE_KEY', None)
        if private_key is None:
            raise ImproperlyConfigured("Please set your XERO_PRIVATE_KEY setting. Must be a path to your privatekey.pem")

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
        contact_id = None
        try:
            result = self.xero.contacts.save(contact_data)
            if len(result) == 1:
                contact_id = result[0]['ContactID']
        except Exception as e:
            raise Exception("Xero Contact Save Failed", e)
        return contact_id

    def add_contact(self, contact_data):
        contact_id = None
        try:
            result = self.xero.contacts.put(contact_data)
            if len(result) == 1:
                contact_id = result[0]['ContactID']
        except Exception as e:
            raise Exception("Xero Contact Save Failed", e)
        return contact_id

    def save_or_put_contact(self, contact_data):
        contact_id = None
        try:
            result = self.xero.contacts.save_or_put(contact_data)
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

    def get_open_invoices(self, user=None):
        if user:
            xero_contact = XeroContact.objects.filter(user=user).first()
            if not xero_contact:
                return None
            return self.xero.invoices.filter(Contact_ContactID=xero_contact.xero_id, Status="AUTHORISED")
        return self.xero.invoices.filter(Status="AUTHORISED")

    def get_open_invoices_by_user(self):
        ''' One call to Xero to pull all open invoices and group them by user '''
        invoices = {}
        for i in self.get_open_invoices(user=None):
            contact_id = i['Contact']['ContactID']
            contact = XeroContact.objects.filter(xero_id=contact_id).first()
            username = "None"
            if contact:
                username = contact.user.username
            if username in invoices:
                invoices[username].append(i)
            else:
                invoices[username] = [i]
        return invoices

    def get_repeating_invoices(self, user):
        xero_data = None
        xero_contact = XeroContact.objects.filter(user=user).first()
        if xero_contact:
            xero_data = self.xero.repeatinginvoices.filter(Contact_ContactID=xero_contact.xero_id)
        return xero_data

    def create_invoice(self):
        # Clearly just a test -- JLS
        xero = self.xero
        invoice = {
                    'Status': 'DRAFT',
                    'Total': '264.00',
                    'CurrencyRate': '1.000000',
                    'Reference': 'sdfghsfgh',
                    'Type': 'ACCREC',
                    'CurrencyCode': 'AUD',
                    'AmountPaid': '0.00',
                    'TotalTax': '24.00',
                    'Contact': {
                        'Name': 'Test One'
                    },
                    'AmountDue': '264.00',
                    'Date': datetime.date(2014, 7, 24),
                    'LineAmountTypes': 'Exclusive',
                    'LineItems': {
                        'LineItem': {
                            'AccountCode': '200',
                            'TaxAmount': '24.00',
                            'Description': 'fgshfsdh',
                            'UnitAmount': '24.00',
                            'TaxType': 'OUTPUT',
                            'ItemCode': 'sfghfshg',
                            'LineAmount': '240.00',
                            'Quantity': '10.0000'
                        }
                    },
                    'SubTotal': '240.00',
                    'DueDate': datetime.date(2014, 7, 24)
                }
        #xero.invoices.put(invoice)
