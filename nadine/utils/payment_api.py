import sys
import hashlib
import random
from datetime import datetime, timedelta

from django.conf import settings

from suds.client import Client

class PaymentAPI:

    def __init__(self):
        url = settings.USA_EPAY_URL2
        key = settings.USA_EPAY_KEY2
        pin = settings.USA_EPAY_PIN2
        self.entry_point = USAEPAY_SOAP_API(url, key, pin)

    def getAllCustomers(self, username):
        return self.entry_point.getAllCustomers(username)

    def get_transactions(self, year, month, day):
        raw_transactions = self.entry_point.getTransactions(year, month, day)
        clean_transactions = clean_transaction_list(raw_transactions)
        return clean_transactions


##########################################################################################
# USAePay SOAP Interface
##########################################################################################


class USAEPAY_SOAP_API:

    def __init__(self, url, key, pin):
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


    def getSearchParam(self, field_name, field_type, field_value):
        param = self.client.factory.create('SearchParam')
        param.Field = field_name
        param.Type = field_type
        param.Value = field_value
        return param


	def getTransactions(self, year, month, day):
		start, end = getDateRange(year, month, day);
		SearchParamArray search = new SearchParamArray();
		search.add(new SearchParam("created", "gte", start));
		search.add(new SearchParam("created", "lte", end));
		return searchTransactions(search);
	}


    def searchTransactions(self, search):
        return searchTransactions(search, true, 0, 100, "created")


    def searchTransactions(self, search, match_all, start, limit, sort_by):
    	result = client.service.searchTransactions(token, search, match_all, start, limit, sort_by)
    	print("searchTransactions: found " + result.getTransactionsReturned())
    	transactionArray = result.getTransactions()
    	return transactionArray.getTransactions()


    def searchCustomers(self, SearchParamArray search, boolean match_all, int start, int limit, String sort_by):
        # TODO
        return None


##########################################################################################
#  Helper functions
##########################################################################################


def getDateRange(year, month, day):
    start = "%s-%s-%s 00:00:00" % (year, month day)
    end = "%s-%s-%s 23:59:59" % (year, month day)
    return (start, end)


def clean_transaction_list(transactions):
    transaction_list = []
    if transactions:
        for t in transactions:
            clean_t = clean_transaction(t)
            transaction_list.append(clean_t)
    return transaction_list


def clean_transaction(t):
        username = t.getCustomerID()
        card_type = t.getCreditCardData().getCardType()
        if not card_type:
            card_type = "ACH"
        status = t.getStatus()
        if status and ' ' in status:
            status = status.split()[0]
        transaction_type = t.getTransactionType()
        amount = t.getDetails().getAmount()
        if transaction_type == 'Credit':
            amount = -1 * amount
        description = t.getDetails().getDescription()
        date_time = datetime.strptime(t.getDateTime(), '%Y-%m-%d %H:%M:%S')
        transaction_id = t.getResponse().getRefNum()
        note = ""
        if status == "Error":
            note = t.getResponse().getError()
        return {'transaction_id': transaction_id, 'username': username, 'transaction': t, 'date_time':date_time, 'description': description,
                'card_type': card_type, 'status': status, 'transaction_type':transaction_type, 'note':note, 'amount': amount}
