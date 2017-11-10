from .base import *

import os
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

PRODUCTION = False
DEBUG = True

# Site Administrators
ADMINS = (
    ('YOU', 'you@yourdomain.com'),
)

# Database Settings
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'nadinedb',
    'USER': 'postgres',
    'PASSWORD': 'password'
}

# Site Information
SITE_NAME = "Nadine"
SITE_DOMAIN = "127.0.0.1:8080"
SITE_PROTO = "http"

# Email Settings
# EMAIL_HOST = "smtp.example.com"
# EMAIL_HOST_USER = "postmaster@example.com"
# EMAIL_HOST_PASSWORD = "password"
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587

# Debug mail server 
# https://docs.djangoproject.com/en/1.11/topics/email/#configuring-email-for-development
EMAIL_PORT = 1025

EMAIL_SUBJECT_PREFIX = "[Nadine] "
SERVER_EMAIL = "nadine@example.com"
DEFAULT_FROM_EMAIL = "nadine@example.com"
STAFF_EMAIL_ADDRESS = "staff@example.com"
BILLING_EMAIL_ADDRESS = "billing@example.com"
TEAM_EMAIL_ADDRESS = "team@example.com"
TEAM_MEMBERSHIP_PACKAGE = "Team Membership"

# Make this unique, and don't share it with anybody.
# http://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = 'YOUR-SECRET-KEY'

#These are business hours used to organize reservations. Times MUST be in military time. Calendar will be broken up via 15 minute increments
OPEN_TIME = '8:00'
CLOSE_TIME = '18:00'

# Country either the 'US' or 'CA' currently for use in user address options
COUNTRY = "US"

# List of possible public calendar designations and the color for display
CALENDAR_DICT = {'Pine':'red', 'Pike': 'RGBA(71, 159, 198, 1)' }

# Allows for the login page to include or not include the option for nonmembers to register and make a user account.
ALLOW_ONLINE_REGISTRATION = False

# Allows or does not allow for users to upload their own profile photo on the edit profile page.
ALLOW_PHOTO_UPLOAD = False

# Apply a discount for members reserving rooms normally charged
MEMBER_DISCOUNT = 0.0

# Google Settings
#GOOGLE_ANALYTICS_ID = "YOUR-GOOGLE-CODE"
#GOOGLE_CALENDAR_ID = "YOUR-GOOGLE-CALENDAR-ID"
#GOOGLE_API_KEY = "YOUR-API-KEY"

# Mailgun Settings
#MAILGUN_API_KEY = "YOUR-MAILGUN-API-KEY"
#MAILGUN_VALIDATION_KEY = "YOUR-MAILGUN-VALIDATION-KEY"
#MAILGUN_DOMAIN = "YOUR-MAILGUN-DOMAIN"
#MAILGUN_DEBUG = False

# USAePay Settings
# Use API Doc/Literal WSDL
#USA_EPAY_GATE = "https://www.usaepay.com/gate.php"
#USA_EPAY_FORM = "https://www.usaepay.com/interface/epayform/"
# Used for adding billing profiles
#USA_EPAY_FORM_KEY="YOUR_KEY"
#USA_EPAY_SOAP_1_2 = "https://www.usaepay.com/soap/gate/YOUR_CODE/usaepay.wsdl"
#USA_EPAY_SOAP_1_4 = "https://www.usaepay.com/soap/gate/YOUR_CODE/usaepay.wsdl"
#USA_EPAY_SOAP_KEY = "YOUR_KEY"
#USA_EPAY_SOAP_PIN = "YOUR_PIN"

# Mailchimp Settings
#MAILCHIMP_API_KEY = "goMonkeygo"
#MAILCHIMP_NEWSLETTER_KEY = "melikekey"
#MAILCHIMP_WEBHOOK_KEY = "hookedonhooks"

# Xero Integration Settings
# Generate an RSA key and register it with Xero as a private application.
# openssl genrsa -out privatekey.pem 1024
# openssl req -new -x509 -key privatekey.pem -out publickey.cer -days 1825
# openssl pkcs12 -export -out public_privatekey.pfx -inkey privatekey.pem -in publickey.cer
#XERO_CONSUMER_KEY = "secretkey"
#XERO_PRIVATE_KEY = "/keys/privatekey.pem"

# Slack Settings
#SLACK_API_TOKEN = "your token"
#SLACK_TEAM_URL = "https://nadine.slack.com/"

# Arp Settings
#ARPWATCH_SNMP_SERVER = '192.168.1.1'
#ARPWATCH_SNMP_COMMUNITY = 'yourcommunitystring'
#ARPWATCH_NETWORK_PREFIX = '192.168.'

# HID Door System
# Encryption Key must be a URL-safe base64-encoded 32-byte key.
# https://cryptography.io/en/latest/fernet/
#HID_ENCRYPTION_KEY = "YOUR-HID-ENCRYPTION-KEY"
#HID_KEYMASTER_URL = "http://127.0.0.1:8000/doors/keymaster/"
#HID_POLL_DELAY_SEC = 60
