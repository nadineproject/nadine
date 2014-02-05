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
		return True
	except:
		return False

def authorize(username, auth_code):
	crypto=AES.new(settings.USA_EPAY_KEY, AES.MODE_ECB)
	decripted_username = urlsafe_b64decode(crypto.decrypt(auth_code))
	padded_username = username[:16].zfill(16)
	return decripted_username == padded_username

def get_auth_code(username):
	crypto=AES.new(settings.USA_EPAY_KEY, AES.MODE_ECB)
	padded_username = username[:16].zfill(16)
	return base64.urlsafe_b64encode(crypto.encrypt(padded_username))