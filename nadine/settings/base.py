# Main settings file for nadine

import os
import sys


################################################################################
# Base Path and Django Settings
################################################################################
# print("Loading global settings file...")

DEBUG = False

# Make this unique, and don't share it with anybody.
# http://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = 'SET_YOUR_SECRET_KEY_IN_LOCAL_SETTINGS'

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

MEDIA_URL = '/media/'
MEDIA_ROOT = path('../media/')

BACKUP_ROOT = path('../backups/')
BACKUP_COUNT = 30

ROOT_URLCONF = 'urls'

DATABASES = {}

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = ('themes/active/static', 'static', )
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'themes/active/templates',
            'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'nadine.context_processors.site',
                'nadine.context_processors.nav_context',
                'nadine.context_processors.tablet_context',
                'nadine.context_processors.allow_online_registration',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]
AUTHENTICATION_BACKENDS = (
    'nadine.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend'
)

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS = [
    # Django Applications
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',
    'django.contrib.messages',
    # Nadine Applications
    'nadine',
    'staff',
    'member',
    'tablet',
    'arpwatch',
    'comlink',
    'doors.keymaster',
    # Other Applications
    'jsignature',
    'taggit_templatetags2',
    'taggit',
    'django_crontab',
    # 'django_extensions',
    # 'debug_toolbar',
]

################################################################################
# Site Settings
################################################################################

SITE_NAME = "Nadine"
SITE_DOMAIN = "localhost"
SITE_PROTO = "http"
SITE_ID = 1

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'
USE_TZ = True

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

# Allows for the login page to include or not include the option for nonmembers to register and make a user account.
ALLOW_ONLINE_REGISTRATION = False

# Allows or does not allow for users to upload their own profile photo on the edit profile page.
ALLOW_PHOTO_UPLOAD = False

# Default billing day for new memberships.  Set to 0 to be the day of the membership.
# DEFAULT_BILLING_DAY = 1
DEFAULT_BILLING_DAY = 0

# List of possible public calendar designations and the color for display. Color can in any color format (name, RGBA, Hex, etc)
# CALENDAR_DICT = {'Pine':'red', 'Pike': 'RGBA(71, 159, 198, 1)' }
CALENDAR_DICT = {}

# The uncommented country below allows for either the US states or Canadian provinces to be options for member profiles.
COUNTRY = 'US'
# COUNTRY = 'CA'

# FACEBOOK_URL = "https://www.facebook.com/OfficeNomads"
# TWITTER_URL = 'https://twitter.com/OfficeNomads'
# YELP_URL = 'https://www.yelp.com/biz/office-nomads-seattle-2'
# INSTAGRAM_URL = 'https://www.instagram.com/officenomads/'

# These are business hours used to organize reservations. Times MUST be in military time. Calendar will be broken up via 15 minute increments
# OPEN_TIME = '8:30'
# CLOSE_TIME = '18:00'

# Apply a discount for members reserving rooms normally charged
MEMBER_DISCOUNT = 0.0

# -- Message of the Day --
# Displayed on the iPad after sign-in
MOTD = "Enjoy your day at Office Nomads!"
MOTD_TIMEOUT = 5000

# Max Upload Size = 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

# URL that handles login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/member/profile/'

# The interface for the front desk tablet.  Values are 'WEB' or "iOS"
#TABLET = "iOS"
TABLET = "WEB"

################################################################################
# Email Settings
# https://docs.djangoproject.com/en/1.11/topics/email/#configuring-email-for-development
################################################################################

# EMAIL_HOST = "smtp.example.com"
# EMAIL_HOST_USER = "postmaster@example.com"
# EMAIL_HOST_PASSWORD = "password"
# EMAIL_USE_TLS = True
# Debug mail server
EMAIL_PORT = 1025
# EMAIL_PORT = 587
EMAIL_SUBJECT_PREFIX = "[Nadine] "
SERVER_EMAIL = "nadine@example.com"
DEFAULT_FROM_EMAIL = "nadine@example.com"
STAFF_EMAIL_ADDRESS = "staff@example.com"
BILLING_EMAIL_ADDRESS = "billing@example.com"
TEAM_EMAIL_ADDRESS = "team@example.com"
TEAM_MEMBERSHIP_PACKAGE = "Team Membership"

EMAIL_VERIFICATION_URL = ''
# EMAIL_VERIFICATION_URL = "https://apps.officenomads.com/mail/verify/%(emailaddress_id)s/%(verif_key)s"
EMAIL_POST_VERIFY_URL = "/member/profile/"

# Mailgun Settings
# MAILGUN_API_KEY = "YOUR-MAILGUN-API-KEY"
# MAILGUN_DOMAIN = "YOUR-MAILGUN-DOMAIN"
# MAILGUN_DEBUG = False

################################################################################

################################################################################
# Other Application Settings
################################################################################

# Arp Watch data directory (This must be in the MEDIA_ROOT)
ARP_ROOT = 'arp_import/'
ARP_IMPORT_LOG = ARP_ROOT + 'import.log'
ARP_IMPORT_LOCK = ARP_ROOT + 'importing.lock'
ARP_IP_PFX = '172.16.5.'
# Arp SNMP Settings
#ARPWATCH_SNMP_SERVER = '192.168.1.1'
#ARPWATCH_SNMP_COMMUNITY = 'yourcommunitystring'
#ARPWATCH_NETWORK_PREFIX = '192.168.'

# JSignature Settings
JSIGNATURE_WIDTH = 500
JSIGNATURE_HEIGHT = 200
JSIGNATURE_COLOR = "30F"
JSIGNATURE_RESET_BUTTON = False
# JSIGNATURE_BACKGROUND_COLOR = "CCC"
# JSIGNATURE_DECOR_COLOR
# JSIGNATURE_LINE_WIDTH
# JSIGNATURE_UNDO_BUTTON = True

# USAePay Settings
# Use API Doc/Literal WSDL
# USA_EPAY_GATE = "https://www.usaepay.com/gate.php"
# USA_EPAY_FORM = "https://www.usaepay.com/interface/epayform/"
# Used for adding billing profiles
# USA_EPAY_FORM_KEY="YOUR_KEY"
# USA_EPAY_SOAP_1_2 = "https://www.usaepay.com/soap/gate/YOUR_CODE/usaepay.wsdl"
# USA_EPAY_SOAP_1_4 = "https://www.usaepay.com/soap/gate/YOUR_CODE/usaepay.wsdl"
# USA_EPAY_SOAP_KEY = "YOUR_KEY"
# USA_EPAY_SOAP_PIN = "YOUR_PIN"

# Stripe Settings
# STRIPE_SECRET_KEY = "sk_XXXXX"
# STRIPE_PUBLISHABLE_KEY = "pk_XXXXX"

# Comlink Settings
COMLINK_UPLOAD_TO = "attachments/"
COMLINK_VERIFY_INCOMING = True
COMLINK_STRIP_EMAILS = False

# Mailchimp Settings
# MAILCHIMP_API_KEY="YourMailchimpKey"
# MAILCHIMP_NEWSLETTER_KEY="YourNewsletter"
# MAILCHIMP_WEBHOOK_KEY = "nadine"

# Google Settings
#GOOGLE_ANALYTICS_ID = "YOUR-GOOGLE-CODE"
#GOOGLE_CALENDAR_ID = "YOUR-GOOGLE-CALENDAR-ID"
#GOOGLE_API_KEY = "YOUR-API-KEY"

################################################################################
# Crontabs - Scheduled Tasks
# https://github.com/kraiz/django-crontab
################################################################################

CRONTAB_LOCK_JOBS = True
CRONTAB_COMMAND_PREFIX = ""
CRONTAB_COMMAND_SUFFIX = ""

CRONJOBS = [
    # Check-in with members
    ('30 8 * * *', 'django.core.management.call_command', ['checkin_anniversary']),
    ('30 8 * * *', 'django.core.management.call_command', ['checkin_exiting']),
    # ('30 8 * * *', 'django.core.management.call_command', ['checkin_two_months']),
    ('30 8 * * *', 'django.core.management.call_command', ['checkin_no_return']),
    ('55 17 * * *', 'django.core.management.call_command', ['checkin_first_day']),
    # Tasks to run every hour
    ('0 * * * *', 'django.core.management.call_command', ['member_alert_check']),
    # Tasks to run every 5 minutes
    ('*/5 * * * *', 'django.core.management.call_command', ['import_arp']),
    ('*/5 * * * *', 'django.core.management.call_command', ['send_user_notifications']),
    # Backup Tasks at 1:00 AM
    ('0 1 * * *', 'django.core.management.call_command', ['backup_members']),
    ('0 1 * * *', 'django.core.management.call_command', ['backup_create']),
    # Billing Tasks at 8:00 PM
    ('0 20 * * *', 'django.core.management.call_command', ['billing_batch_run']),
    # Other Tasks
    ('30 8 * * *', 'django.core.management.call_command', ['announce_special_days']),
]

################################################################################
# Logging
################################################################################

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': path('../django.log'),
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django_crontab': {
            'handlers': ['file', 'console', 'mail_admins'],
            'level': 'INFO',
        },
        'nadine': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'staff': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # 'arpwatch': {
        #     'handlers': ['file'],
        #     'level': 'INFO',
        # },
    },
}


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
