import base64
from py4j.java_gateway import JavaGateway
from Crypto.Cipher import AES
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
    transactions = []
    gateway = JavaGateway()
    gateway_transactions = gateway.entry_point.getTransactions(year, month, day)
    if gateway_transactions:
        for t in gateway_transactions:
            username = t.getCustomerID()
            card_type = t.getCreditCardData().getCardType()
            if not card_type:
                card_type = "ACH"
            status = t.getStatus()
            if status and ' ' in status:
                status = status.split()[0]
            amount = t.getDetails().getAmount()
            description = t.getDetails().getDescription()
            transactions.append({'username': username, 'transaction': t, 'description': description,
                                 'card_type': card_type, 'status': status, 'amount': amount})
    return transactions


def authorize(username, auth_code):
    crypto = AES.new(settings.USA_EPAY_KEY, AES.MODE_ECB)
    decripted_username = urlsafe_b64decode(crypto.decrypt(auth_code))
    padded_username = username[:16].zfill(16)
    return decripted_username == padded_username


def get_auth_code(username):
    crypto = AES.new(settings.USA_EPAY_KEY, AES.MODE_ECB)
    padded_username = username[:16].zfill(16)
    return base64.urlsafe_b64encode(crypto.encrypt(padded_username))
