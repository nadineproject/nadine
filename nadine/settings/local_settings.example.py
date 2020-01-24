################################################################################
# Example Local Settings File
#
# Override default settings here.
# For a complete list of settings, see base.py
################################################################################

from nadine.settings.base import *

PRODUCTION = False
DEBUG = True

# Site Administrators
ADMINS = [
    ('YOU', 'you@yourdomain.com'),
]

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
COUNTRY = "US"
TIME_ZONE = 'UTC'

# Email Settings
EMAIL_HOST = "smtp.example.com"
EMAIL_HOST_USER = "postmaster@example.com"
EMAIL_HOST_PASSWORD = "password"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_SUBJECT_PREFIX = "[Nadine] "
SERVER_EMAIL = "nadine@example.com"
DEFAULT_FROM_EMAIL = "nadine@example.com"
STAFF_EMAIL_ADDRESS = "staff@example.com"
BILLING_EMAIL_ADDRESS = "billing@example.com"
TEAM_EMAIL_ADDRESS = "team@example.com"
TEAM_MEMBERSHIP_PACKAGE = "Team Membership"

# Site Key - Keep safe!
SECRET_KEY = 'YOUR-SECRET-KEY'
