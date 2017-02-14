# Django settings for django_apps project.
import os
import sys

from datetime import timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)
print("Loading global settings file...")

# TEMPLATE_DIRS = (path('../templates/'), )
MEDIA_URL = '/media/'
MEDIA_ROOT = path('../media/')

BACKUP_ROOT = path('../backups/')
BACKUP_COUNT = 30

SITE_NAME = "Nadine"
SITE_DOMAIN = "localhost"
SITE_PROTO = "http"
SITE_ID = 1

STATIC_URL = '/static/'
STATICFILES_DIRS = ('themes/active/static', 'static', )
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

DEBUG = False

SECRET_KEY = 'SET_YOUR_SECRET_KEY_IN_LOCAL_SETTINGS'

# -- Message of the Day --
# Displayed on the iPad after sign-in
MOTD = "Enjoy your day at Office Nomads!"
MOTD_TIMEOUT = 5000

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/media/'

# 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

# Arp Watch data directory (This must be in the MEDIA_ROOT)
ARP_ROOT = 'arp_import/'
ARP_IMPORT_LOG = ARP_ROOT + 'import.log'
ARP_IMPORT_LOCK = ARP_ROOT + 'importing.lock'
ARP_IP_PFX = '172.16.5.'

# URL that handles login
LOGIN_URL = '/login/'

# The interface for the front desk tablet.  Values are 'WEB' or "iOS"
#TABLET = "iOS"
TABLET = "WEB"

# Auth Backends
AUTHENTICATION_BACKENDS = (
    'nadine.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend'
)

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

# TEMPLATE_CONTEXT_PROCESSORS = (
#     "django.contrib.auth.context_processors.auth",
#     "django.core.context_processors.debug",
#     "django.core.context_processors.i18n",
#     "django.core.context_processors.media",
#     "django.core.context_processors.static",
#     "django.core.context_processors.request",
#     "django.contrib.messages.context_processors.messages",
# )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'nadine',
    'staff',
    'members',
    'comlink',
    'interlink',
    'arpwatch',
    'tablet',
    'easy_pdf',
    'jsignature',
    'taggit_templatetags2',
    'taggit',
    'djcelery',
    'doors.keymaster',
]

#
# Celery initialization
#
try:
    import djcelery
    djcelery.setup_loader()
except ImportError:
    pass

# Multimail settings
# https://github.com/scott2b/django-multimail
#MULTIMAIL_FROM_EMAIL_ADDRESS = ''
#MULTIMAIL_EMAIL_VERIFICATION_URL = "https://apps.officenomads.com/mail/verify/%(emailaddress_id)s/%(verif_key)s"
#MULTIMAIL_FROM_EMAIL_ADDRESS = 'nadine@officenomads.com"
EMAIL_VERIFICATION_URL = ''
EMAIL_POST_VERIFY_URL = "/members/profile/"

# JSignature Settings
JSIGNATURE_WIDTH = 500
JSIGNATURE_HEIGHT = 200
JSIGNATURE_COLOR = "30F"
#JSIGNATURE_BACKGROUND_COLOR = "CCC"
# JSIGNATURE_DECOR_COLOR
# JSIGNATURE_LINE_WIDTH
#JSIGNATURE_UNDO_BUTTON = True
JSIGNATURE_RESET_BUTTON = False

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

# Comlink Settings
MAILGUN_UPLOAD_TO = "attachments/"
MAILGUN_VERIFY_INCOMING = True

# Mailgun Settings
#MAILGUN_API_KEY = "YOUR-MAILGUN-API-KEY"
#MAILGUN_DOMAIN = "YOUR-MAILGUN-DOMAIN"
#MAILGUN_DEBUG = False

# Celery Settings
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_DISABLE_RATE_LIMITS = True
CELERY_RESULT_BACKEND = "amqp"
BROKER_URL = "amqp://guest:guest@localhost:5672//"
CELERY_TIMEZONE = 'America/Los_Angeles'

# When this is True, celery tasks will be run synchronously.
# This is nice when running unit tests or in development.
# In production set this to False in your local_settings.py
CELERY_ALWAYS_EAGER = False

# MAILCHIMP_API_KEY="YourMailchimpKey"
# MAILCHIMP_NEWSLETTER_KEY="YourNewsletter"
#MAILCHIMP_WEBHOOK_KEY = "nadine"

# Allows for the login page to include or not include the option for nonmembers to register and make a user account.
ALLOW_ONLINE_REGISTRATION = False

# Allows or does not allow for users to upload their own profile photo on the edit profile page.
ALLOW_PHOTO_UPLOAD = False

# List of possible public calendar designations and the color for display. Color can in any color format (name, RGBA, Hex, etc)
CALENDAR_DICT = {}

# The uncommented country below allows for either the US states or Canadian provinces to be options for member profiles.
COUNTRY = 'US'
# COUNTRY = 'CA'

# Uncomment and insert social media URLS to be inserted in the footer
#FACEBOOK_URL = "https://www.facebook.com/OfficeNomads"
#TWITTER_URL = 'https://twitter.com/OfficeNomads'
#YELP_URL = 'https://www.yelp.com/biz/office-nomads-seattle-2'
#INSTAGRAM_URL = 'https://www.instagram.com/officenomads/'

# These are business hours used to organize reservations. Times MUST be in military time. Calendar will be broken up via 15 minute increments
# OPEN_TIME = '8:30'
# CLOSE_TIME = '18:00'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Logging
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
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
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

# Import the local and theme SETTINGS files
if os.path.isfile('nadine/local_settings.py'):
    #print("Loading local settings file...")
    from nadine.local_settings import *
if os.path.isfile('themes/active/theme_settings.py'):
    #print("Loading theme settings file...")
    import imp
    sys.path.append('themes/active')
    theme_settings = imp.load_source('themes.active.theme_settings', 'themes/active/theme_settings.py')
    from theme_settings import *


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
