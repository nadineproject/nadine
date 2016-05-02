import sys
import csv
import base64
import random
import hashlib
from datetime import datetime, timedelta
from collections import OrderedDict

from django.conf import settings

from suds.client import Client


class PaymentAPI(object):

    def __init__(self):
        url = settings.USA_EPAY_URL2
        key = settings.USA_EPAY_KEY2
        pin = settings.USA_EPAY_PIN2
        self.entry_point = USAEPAY_SOAP_API(url, key, pin)

    def get_customers(self, username):
    	search = SearchParamArray(self.entry_point.client)
    	search.addParameter("CustomerID", "eq", username)
        return self.entry_point.searchCustomers(search)[0][0]

    def get_transactions(self, year, month, day):
        raw_transactions = self.entry_point.getTransactions(year, month, day)
        clean_transactions = clean_transaction_list(raw_transactions)
        return clean_transactions

    def get_checks_settled_by_date(self, year, month, day):
        results = self.entry_point.getTransactionReport("check:settled by date", year, month, day)

        # We pull another report to find any returned checks
        # I'm not sure why this isn't in the error report but I have to go through all transactions
        report2 = self.entry_point.getTransactionReport("check:All Transactions by Date", year, month, day)
        return report2
        for row in report2:
            if row['status'] == "Returned":
                results.append(row)

        return results

    def get_history(self, username):
        # Searches all the history for all the customers for this user
        # Returns a dictionary of {cust_num: transactions}
        history = OrderedDict()
        for cust in self.get_customers(username):
            raw_transactions = self.entry_point.getCustomerHistory(cust.CustNum)
            clean_transactions = clean_transaction_list(raw_transactions)
            history[cust] = clean_transactions
        return history

    def close_current_batch(self):
        pass

    def runSale(self, customer_id, amount, invoice, description, comments):
        if amount <= 0:
            raise Exception("Invalid amount (%s)!" % amount)
        self.entry_point.runSale(int(customer_id), float(amount), invoice, description, comments)

    def update_recurring(self, customer_id, enabled, next_date, description, comment, amount):
        customer_object = self.entry_point.getCustomer(customer_id)
        customer_object.Enabled = enabled
        customer_object.Next = next_date
        customer_object.Description = description
        customer_object.Amount = amount
        customer_object.ReceiptNote = comment
        customer_object.SendReceipt = True
        return self.entry_point.updateCustomer(customer_object)

    def disableAutoBilling(self, username):
        for cust in self.get_customers(username):
            cust.Enabled = False
            self.entry_point.updateCustomer(cust)


##########################################################################################
#  Helper functions
##########################################################################################


def getDateRange(year, month, day):
    start = "%s-%s-%s 00:00:00" % (year, month, day)
    end = "%s-%s-%s 23:59:59" % (year, month, day)
    return (start, end)


def clean_transaction_list(transactions):
    transaction_list = []
    if transactions:
        for t in transactions:
            clean_t = clean_transaction(t)
            transaction_list.append(clean_t)
    return transaction_list


def clean_transaction(t):
        username = t.CustomerID
        if t.CreditCardData:
            card_type = t.CreditCardData.CardType
        else:
            card_type = "ACH"
        status = t.Status
        if status and ' ' in status:
            status = status.split()[0]
        transaction_type = t.TransactionType
        amount = t.Details.Amount
        if transaction_type == 'Credit':
            amount = -1 * amount
        description = t.Details.Description
        date_time = datetime.strptime(t.DateTime, '%Y-%m-%d %H:%M:%S')
        transaction_id = t.Response.RefNum
        note = ""
        if status == "Error":
            note = t.Response.Error
        return {'transaction_id': transaction_id, 'username': username, 'transaction': t, 'date_time':date_time, 'description': description,
                'card_type': card_type, 'status': status, 'transaction_type':transaction_type, 'note':note, 'amount': amount}


##########################################################################################
# USAePay SOAP Interface
##########################################################################################


class SearchParamArray(object):

    def __init__(self, soap_client):
        self.soap_client = soap_client
        self.soap_object = soap_client.factory.create('SearchParamArray')

    def addParameter(self, field_name, field_type, field_value):
        param = self.soap_client.factory.create('SearchParam')
        param.Field = field_name
        param.Type = field_type
        param.Value = field_value
        self.soap_object.SearchParam.append(param)

    def to_soap(self):
        return self.soap_object


class USAEPAY_SOAP_API(object):

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
        return self.client.service.searchCustomerID(self.token, username)

    def getCustomer(self, customer_number):
        return self.client.service.getCustomer(self.token, int(customer_number))

    def updateCustomer(self, customer):
        customer_number = customer.CustNum
        return self.client.service.updateCustomer(self.token, customer_number, customer)

    def getTransactions(self, year, month, day):
        start, end = getDateRange(year, month, day)
        search = SearchParamArray(self.client)
        search.addParameter("created", "gte", start)
        search.addParameter("created", "lte", end)
        return self.searchTransactions(search);

    def getCustomerHistory(self, customer_number):
        result = self.client.service.getCustomerHistory(self.token, customer_number)
        return result.Transactions[0]

    def searchTransactions(self, search, match_all=True, start=0, limit=100, sort_by=None):
        if not sort_by:
            sort_by = "created"
    	result = self.client.service.searchTransactions(self.token, search.to_soap(), match_all, start, limit, sort_by)
        return result.Transactions[0]

    def getTransactionReport(self, report_type, year, month, day):
        start, end = getDateRange(year, month, day)
        response = self.client.service.getTransactionReport(self.token, start, end, report_type, "csv")
        report_csv = base64.b64decode(response)
        row_list = list(csv.reader(report_csv.splitlines(), delimiter=','))
        # First row is the header which we could use, but I like my simplified headers better
        row_list.pop(0)
        results = []
        for row in row_list:
            results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
        return results

    def searchCustomers(self, search, match_all=True, start=0, limit=100, sort_by=None):
        if not sort_by:
            sort_by = "created"
        result = self.client.service.searchCustomers(self.token, search.to_soap(), match_all, start, limit, sort_by)
        return result

    def emailReceipt(self, transaction_id):
        response = self.client.service.emailTransactionReceipt(self.token, transaction_id)

    def runSale(self, customer_number, amount, invoice, description, comments):
        params = self.client.factory.create('CustomerTransactionRequest')
        params.Command = "Sale"
        params.CustReceipt = True
        params.MerchReceipt = True
        params.Details.Amount = float(amount)
        params.Details.Invoice = invoice
        params.Details.Description = description
        params.Details.Comments = comments
        print params

        paymentID = 0 # sets it to use default
        response = self.client.service.runCustomerTransaction(self.token, customer_number, paymentID, params)
        return response

    def updateRecurring(self, customer_number, enabled, next_date, description, comment, amount):
        customer_object = self.getCustomer(customer_number)
        customer_object.Enabled = enabled
        customer_object.Next = next_date
        customer_object.Description = description
        customer_object.Amount = amount
        customer_object.ReceiptNote = comment
        customer_object.SendReceipt = True
        self.updateCustomer(customer_object)
