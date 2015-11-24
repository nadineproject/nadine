import base64, csv
from datetime import datetime, timedelta
from py4j.java_gateway import JavaGateway
from django.conf import settings

def disableAutoBilling(username):
    try:
        gateway = JavaGateway()
        gateway.entry_point.disableAll(username)
        return True
    except:
        return False


def getAllCustomers(username):
    try:
        gateway = JavaGateway()
        return gateway.entry_point.getAllCustomers(username)
    except:
        return None


def getAllEnabledCustomers():
    try:
        gateway = JavaGateway()
        return gateway.entry_point.getEnabledCustomers()
    except:
        return None


def auto_bill_enabled(username):
    try:
        gateway = JavaGateway()
        for cust in gateway.entry_point.getAllCustomers(username):
            if cust.isEnabled():
                return True
    except:
        return None
    return False


def get_transactions(year, month, day):
    gateway = JavaGateway()
    raw_transactions = gateway.entry_point.getTransactions(year, month, day)
    clean_transactions = clean_transaction_list(raw_transactions)
    return clean_transactions


def get_history(username):
    # Searches all the history for all the customers for this user
    # Returns a dictionary of {cust_num: transactions}
    history = {}
    try:
        gateway = JavaGateway()
        for cust in gateway.entry_point.getAllCustomers(username):
            cust_num = cust.getCustNum()
            raw_transactions = gateway.entry_point.getCustomerHistory(int(cust_num))
            clean_transactions = clean_transaction_list(raw_transactions)
            history[cust_num] = clean_transactions
    except:
        return None
    
    return history


def has_new_card(username):
    history = get_history(username)
    for cust_num, transactions in history.items():
        # New cards have only a few transactions and one
        # is an autorization within one week
        if len(transactions) <= 3:
            auth = transactions[0]['status'] == 'Authorized'
            recent = datetime.now() - transactions[0]['date_time'] <= timedelta(weeks=1)
            return auth and recent
    return False


def clean_transaction_list(transactions):
    transaction_list = []
    if transactions:
        for t in transactions:
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
            transaction_list.append({'username': username, 'transaction': t, 'date_time':date_time, 'description': description,
                                 'card_type': card_type, 'status': status, 'transaction_type':transaction_type, 'amount': amount})
    return transaction_list


def get_checks_settled_by_date(year, month, day):
    gateway = JavaGateway()
    report = gateway.entry_point.getTransactionReport("check:settled by date", year, month, day)
    row_list = list(csv.reader(report.splitlines(), delimiter=','))
    row_list.pop(0)
    results = []
    for row in row_list:
        results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
    # We pull another report to find any returned checks
    # I'm not sure why this isn't in the error report but I have to go through all transactions
    report = gateway.entry_point.getTransactionReport("check:All Transactions by Date", year, month, day)
    row_list = list(csv.reader(report.splitlines(), delimiter=','))
    row_list.pop(0)
    for row in row_list:
        if row[9] == "Returned":
            results.append({'date':row[1], 'name':row[2], 'status':row[9], 'amount':row[10], 'processed':row[13]})
    return results


def get_auth_code(username):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    padded_username = username[:16].zfill(16)
    aes = algorithms.AES(settings.USA_EPAY_KEY)
    backend = default_backend()
    cipher = Cipher(aes, modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(str(padded_username)) + encryptor.finalize()
    return base64.urlsafe_b64encode(ct)
