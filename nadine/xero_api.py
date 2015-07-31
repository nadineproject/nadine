from xero import Xero
from xero.auth import PrivateCredentials

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

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

    def save_contact(self, user):
        contact_data = self.get_contact(user)
        # TODO fill contact data with data from user
        # This is just a test --JLS
        self.xero.contacts.save_or_put(contact_data)

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