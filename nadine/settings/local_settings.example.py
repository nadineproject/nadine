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
SITE_URL = "http://127.0.0.1:8080"
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

# Nextcloud Settings
NEXTCLOUD_HOST = 'cloud.example.com'
NEXTCLOUD_ADMIN = 'admin'
NEXTCLOUD_PASSWORD = 'password'
NEXTCLOUD_USE_HTTPS = True
NEXTCLOUD_SSL_IS_SIGNED = True
NEXTCLOUD_USER_SEND_EMAIL_PASSWORD = True
NEXTCLOUD_USER_GROUP = None
NEXTCLOUD_USER_QUOTA = '100GB'

# Rocketchat Setings
ROCKETCHAT_HOST = 'demo.rocket.chat'
ROCKETCHT_ADMIN = 'user'
ROCKETCHAT_SECRET = 'pass'
ROCKETCHAT_USE_HTTPS = True
ROCKETCHAT_SSL_IS_SIGNED = True
ROCKETCHAT_SEND_WELCOME_MAIL = False
ROCKETCHAT_REQUIRE_CHANGE_PASS = False
ROCKETCHAT_VERIFIED_USER = False
ROCKETCHAT_USER_GROUP = None  # array()

# Site Key - Keep safe!
SECRET_KEY = 'YOUR-SECRET-KEY'
