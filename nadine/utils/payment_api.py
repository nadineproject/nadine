import sys
import csv
import base64
import random
import hashlib
import logging
from datetime import datetime, timedelta
from collections import OrderedDict

from django.conf import settings

from suds.client import Client


class PaymentAPI(object):

    def __init__(self, v=4):
        if not hasattr(settings, 'USA_EPAY_SOAP_KEY'):
            self.enabled = False
            return None

        self.enabled = True
        if v == 2:
            self.url = settings.USA_EPAY_SOAP_1_2
        elif v == 3:
            self.url = settings.USA_EPAY_SOAP_1_3
        elif v == 6:
            self.url = settings.USA_EPAY_SOAP_1_6
        else:
            self.url = settings.USA_EPAY_SOAP_1_4
        self.entry_point = USAEPAY_SOAP_API(self.url, settings.USA_EPAY_SOAP_KEY, settings.USA_EPAY_SOAP_PIN)

    def switch_api_ver(self, version):
        self.__init__(v=version)

    def get_customers(self, username):
        customers = self.entry_point.getAllCustomers(username)
        if not customers:
            return []
        return customers

    def get_transactions(self, year, month, day):
        raw_transactions = self.entry_point.getTransactions(year, month, day)
        clean_transactions = clean_transaction_list(raw_transactions)
        return clean_transactions

    def get_checks_settled_by_date(self, year, month, day):
        raw_transactions = self.entry_point.getSettledCheckTransactions(year, month, day)
        clean_transactions = clean_transaction_list(raw_transactions)
        return clean_transactions

    def get_history(self, username):
        # Searches all the history for all the customers for this user
        # Returns a dictionary of {cust_num: transactions}
        history = OrderedDict()
        for cust in self.get_customers(username):
            raw_transactions = self.entry_point.getCustomerHistory(cust.CustNum)
            clean_transactions = clean_transaction_list(raw_transactions)
            history[cust] = clean_transactions
        return history

    def run_transaction(self, customer_id, amount, description, invoice=None, comment=None, auth_only=False):
        if float(amount) <= 0:
            raise Exception("Invalid amount (%s)!" % amount)

        # We have to revert to API v1.2 to make this work HACK!!!!!!
        self.switch_api_ver(2)
        response = self.entry_point.runTransaction2(int(customer_id), float(amount), description, invoice=invoice, comment=comment, auth_only=auth_only)
        transaction_id = response.RefNum

        # Stupid 1.2 api doesn't send the email so we'll do it manually
        self.switch_api_ver(4)
        customer = self.entry_point.getCustomer(customer_id)
        email = customer.BillingAddress.Email
        if email:
            self.email_receipt(transaction_id, email)

        return response

    def void_transaction(self, username, transaction_id):
        t = self.get_transaction(transaction_id)
        if t['username'] == username and t['status'] == "Authorized":
            return self.entry_point.voidTransaction(transaction_id)
        return False

    def get_transaction(self, transaction_id, clean=True):
        transaction = self.entry_point.getTransaction(transaction_id)
        if clean:
            return clean_transaction(transaction)
        return transaction

    def update_billing_details(self, customer_id, address, zipcode, email):
        customer_object = self.entry_point.getCustomer(customer_id)
        customer_object.BillingAddress.Street = address
        customer_object.BillingAddress.Zip = zipcode
        customer_object.BillingAddress.Email = email
        return self.entry_point.updateCustomer(customer_object)

    def update_recurring(self, customer_id, enabled, next_date, description, comment, amount):
        customer_object = self.entry_point.getCustomer(customer_id)
        customer_object.Enabled = enabled
        customer_object.Next = next_date
        customer_object.Description = description
        customer_object.Amount = amount
        customer_object.ReceiptNote = comment
        customer_object.SendReceipt = True
        return self.entry_point.updateCustomer(customer_object)

    def disable_recurring(self, username):
        for cust in self.get_customers(username):
            try:
                cust.Enabled = False
                self.entry_point.updateCustomer(cust)
            except Exception as e:
                pass

    def auto_bill_enabled(self, username):
        for cust in self.get_customers(username):
            if cust.Enabled:
                return True
        return False

    def has_new_card(self, username):
        history = self.get_history(username)
        for cust_num, transactions in list(history.items()):
            # New cards have only a few transactions and one
            # is an autorization within one week
            if len(transactions) > 0 and len(transactions) <= 3:
                auth = transactions[0]['status'] == 'Authorized'
                recent = datetime.now() - transactions[0]['date_time'] <= timedelta(weeks=1)
                if auth and recent:
                    return True
        return False

    def email_receipt(self, transaction_id, email):
        self.entry_point.emailReceipt(transaction_id, email, receipt_name="vterm_customer")
        if settings.BILLING_EMAIL_ADDRESS:
            self.entry_point.emailReceipt(transaction_id, settings.BILLING_EMAIL_ADDRESS, receipt_name="vterm_merchant")

    def close_current_batch(self):
        self.entry_point.closeCurrentBatch()


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
        if "CardType" in t.CreditCardData:
            card_type = t.CreditCardData.CardType
        else:
            card_type = "U"
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
        salt = random.randint(0, sys.maxsize)
        salted_value = "%s%s%s" % (key, salt, pin)
        pin_hash = hashlib.sha1(salted_value.encode('utf-8'))

        self.token = self.client.factory.create('ueSecurityToken')
        self.token.SourceKey = key
        self.token.PinHash.Type = 'sha1'
        self.token.PinHash.Seed = salt
        self.token.PinHash.HashValue = pin_hash.hexdigest()

    def getCustomerNumber(self, username):
        return self.client.service.searchCustomerID(self.token, username)

    def getCustomer(self, customer_number):
        return self.client.service.getCustomer(self.token, int(customer_number))

    def getAllCustomers(self, username):
        search = SearchParamArray(self.client)
        search.addParameter("CustomerID", "eq", username)
        result = self.searchCustomers(search)
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None

    def updateCustomer(self, customer):
        customer_number = customer.CustNum
        return self.client.service.updateCustomer(self.token, customer_number, customer)

    def getTransactions(self, year, month, day):
        start, end = getDateRange(year, month, day)
        search = SearchParamArray(self.client)
        search.addParameter("created", "gte", start)
        search.addParameter("created", "lte", end)
        return self.searchTransactions(search)

    def getTransaction(self, transaction_id):
        transaction_object = self.client.service.getTransaction(self.token, transaction_id)
        return transaction_object

    def getSettledCheckTransactions(self, year, month, day):
        start, end = getDateRange(year, month, day)
        search = SearchParamArray(self.client)
        search.addParameter("VCChecks.Settled", "gte", start)
        search.addParameter("VCChecks.Settled", "lte", end)
        return self.searchTransactions(search)

    def getCustomerHistory(self, customer_number):
        result = self.client.service.getCustomerHistory(self.token, customer_number)
        if len(result.Transactions) >= 1:
            return result.Transactions[0]
        return None

    def searchTransactions(self, search, match_all=True, start=0, limit=100, sort_by=None):
        if not sort_by:
            sort_by = "created"
        result = self.client.service.searchTransactions(self.token, search.to_soap(), match_all, start, limit, sort_by)
        if len(result.Transactions) >= 1:
            return result.Transactions[0]
        return None

    # This isn't working.  There is a bug in USAePay and it's been reported. --JLS
    # def getTransactionReport(self, report_type, year, month, day):
    #     start, end = getDateRange(year, month, day)
    #     response = self.client.service.getTransactionReport(self.token, start, end, report_type, "csv")
    #     report_csv = base64.b64decode(response)
    #     row_list = list(csv.reader(report_csv.splitlines(), delimiter=','))
    #     # First row is the header which we could use, but I like my simplified headers better
    #     row_list.pop(0)
    #     results = []
    #     for row in row_list:
    #         results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
    #     return results

    def searchCustomers(self, search, match_all=True, start=0, limit=100, sort_by=None):
        if not sort_by:
            sort_by = "created"
        result = self.client.service.searchCustomers(self.token, search.to_soap(), match_all, start, limit, sort_by)
        return result

    def emailReceipt(self, transaction_id, email_address, receipt_name=None):
        if not receipt_name:
            receipt_name = "vterm_customer"
        response = self.client.service.emailTransactionReceiptByName(self.token, transaction_id, receipt_name, email_address)
        if not response:
            raise Exception("Sending email failed!")
        return response

    # Depricated in favor of runTransaction(auth_only=True)
    # def authorize(self, customer_number):
    #     params = self.client.factory.create('CustomerTransactionRequest')
    #     params.Command = "AuthOnly"
    #     params.CustReceipt = True
    #     params.MerchReceipt = True
    #     details = self.client.factory.create('TransactionDetail')
    #     details.Amount = 1.00
    #     details.Description = "Office Nomads Authorization"
    #     params.Details = details
    #     paymentID = 0 # sets it to use default
    #     response = self.client.service.runCustomerTransaction(self.token, customer_number, paymentID, params)
    #     if response.Error:
    #         raise Exception(response.Error)
    #     return response

    # 1.2 way of doing things
    def runTransaction2(self, customer_number, amount, description, invoice=None, comment=None, auth_only=False):
        params = self.client.factory.create('CustomerTransactionDetail')

        if auth_only:
            command = "AuthOnly"
        else:
            command = "Sale"
        params.Amount = float(amount)
        params.Description = description
        if invoice:
            params.Invoice = invoice
        if comment:
            params.Comments = comment

        paymentID = int(0) # sets it to use default
        response = self.client.service.runCustomerTransaction(self.token, int(customer_number), params, command, paymentID)
        return response

    # 1.4 way of doing things
    def runTransactions4(self, customer_number, amount, description, invoice=None, comment=None, auth_only=False):
        params = self.client.factory.create('CustomerTransactionRequest')

        if auth_only:
            command = "AuthOnly"
        else:
            command = "Sale"
        params.CustReceipt = True
        params.MerchReceipt = True
        params.Command = command
        params.Details.Amount = float(amount)
        params.Details.Description = description
        if invoice:
            params.Details.Invoice = invoice
        if comment:
            params.Details.Comments = comment

        paymentID = int(0) # sets it to use default
        response = self.client.service.runCustomerTransaction(self.token, int(customer_number), paymentID, params)
        if response.Error:
            raise Exception(response.Error)
        return response

    def voidTransaction(self, transaction_id):
        response = self.client.service.voidTransaction(self.token, transaction_id)
        if response == False:
            raise Exception("Could not void transaction.  No error given.")
        elif hasattr(response, 'Error'):
            raise Exception(response.Error)
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

    def closeCurrentBatch(self):
        # Setting batch number to 0 for current batch
        return self.closeBatch(0)

    def closeBatch(self, batch_number):
        response = self.client.service.closeBatch(self.token, batch_number)
        return response
