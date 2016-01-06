import base64, csv
from datetime import datetime, timedelta
from py4j.java_gateway import JavaGateway
from django.conf import settings
from collections import OrderedDict

class EPayAPI:
    
    def __init__(self):
        self.gateway = JavaGateway()
        self.entry_point = self.gateway.entry_point


    def disableAutoBilling(self, username):
        try:
            self.entry_point.disableAll(username)
            return True
        except Exception:
            return False


    def getAllCustomers(self, username):
        return self.entry_point.getAllCustomers(username)

    def getAllEnabledCustomers(self):
        return self.entry_point.getEnabledCustomers()


    def auto_bill_enabled(self, username):
        for cust in self.entry_point.getAllCustomers(username):
            if cust.isEnabled():
                return True
        return False


    def update_customer(self, customer_id, address, zip_code, email):
        fields = self.gateway.jvm.java.util.HashMap()
        fields['Address'] = address
        fields['Zip'] = zip_code
        fields['Email'] = email
        return self.entry_point.updateCustomer(customer_id, fields)


    def update_recurring(self, customer_id, enabled, next_date, description, amount):
        fields = self.gateway.jvm.java.util.HashMap()
        fields['Enabled'] = str(enabled)
        fields['Next'] = next_date
        fields['Description'] = description
        fields['Amount'] = amount
        fields['SendReceipt'] = 'True'
        return self.entry_point.updateCustomer(int(customer_id), fields)


    def get_transactions(self, year, month, day):
        raw_transactions = self.entry_point.getTransactions(year, month, day)
        clean_transactions = clean_transaction_list(raw_transactions)
        return clean_transactions


    def get_history(self, username):
        # Searches all the history for all the customers for this user
        # Returns a dictionary of {cust_num: transactions}
        history = OrderedDict()
        customers = self.entry_point.getAllCustomers(username)
        for cust in customers:
            cust_num = cust.getCustNum()
            raw_transactions = self.entry_point.getCustomerHistory(int(cust_num))
            clean_transactions = clean_transaction_list(raw_transactions)
            history[cust] = clean_transactions
        return history


    def has_new_card(self, username):
        history = get_history(username)
        for cust_num, transactions in history.items():
            # New cards have only a few transactions and one
            # is an autorization within one week
            if len(transactions) <= 3:
                auth = transactions[0]['status'] == 'Authorized'
                recent = datetime.now() - transactions[0]['date_time'] <= timedelta(weeks=1)
                return auth and recent
        return False


    def update_customer(self, custID, fields):
        pass


    def get_checks_settled_by_date(self, year, month, day):
        report = self.entry_point.getTransactionReport("check:settled by date", year, month, day)
        row_list = list(csv.reader(report.splitlines(), delimiter=','))
        row_list.pop(0)
        results = []
        for row in row_list:
            results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
        # We pull another report to find any returned checks
        # I'm not sure why this isn't in the error report but I have to go through all transactions
        report = self.entry_point.getTransactionReport("check:All Transactions by Date", year, month, day)
        row_list = list(csv.reader(report.splitlines(), delimiter=','))
        row_list.pop(0)
        for row in row_list:
            if row[9] == "Returned":
                results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
        return results


    def get_transaction(self, transaction_id):
        transaction = self.entry_point.getTransaction(transaction_id)
        return clean_transaction(transaction)


    def void_transaction(self, username, transaction_id):
        t = clean_transaction(self.entry_point.getTransaction(transaction_id))
        if t['username'] == username and t['status'] == "Authorized":
            return self.entry_point.voidTransaction(transaction_id)
        return False


    def get_auth_code(self, username):
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        padded_username = username[:16].zfill(16)
        aes = algorithms.AES(settings.USA_EPAY_KEY)
        backend = default_backend()
        cipher = Cipher(aes, modes.ECB(), backend=backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(str(padded_username)) + encryptor.finalize()
        return base64.urlsafe_b64encode(ct)

##########################################################################################
#  Helper functions
##########################################################################################


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

