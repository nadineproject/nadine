# Additional settings required for ldap_sync

from nadine.settings.base import *


# Application definition
#
INSTALLED_APPS += [
    'ldap_sync.apps.LDAPSyncConfig',
]

# Overriding Django Auth's hashers with those from PassLib
django_contrib_auth_index = INSTALLED_APPS.index('django.contrib.auth')
INSTALLED_APPS.insert(django_contrib_auth_index + 1, 'passlib.ext.django')

# Cron tasks
#
CRONJOBS += [
    # Run LDAP sync every 15 mins:
    ('*/15 * * * *', 'django.core.management.call_command', ['syncldapusers']),
]

# LDAP Database (for creating & updating LDAP records)
# https://github.com/django-ldapdb/django-ldapdb#using-django-ldapdb
#
DATABASES['ldap'] = {
    'ENGINE': 'ldapdb.backends.ldap',
    'NAME': 'ldap://localhost',
    'USER': 'cn=admin,dc=312main,dc=ca',
    'PASSWORD': '',
}
DATABASE_ROUTERS = ['ldapdb.router.Router']
# Base LDAP DN (location) to read/write user accounts
LDAP_SYNC_USER_BASE_DN = "ou=users,dc=example,dc=com"
LDAP_SYNC_GROUP_BASE_DN = "ou=groups,dc=example,dc=com"
LDAP_SYNC_MEMBERS_GROUP_CN = "members"
LDAP_SYNC_USER_HOME_DIR_TEMPLATE = "/home/{}"

# PassLib provides LDAP-compatible password hashing, hash formatting and authentication.
PASSLIB_CONFIG = {
    'schemes': [
        'ldap_pbkdf2_sha256',
        # SHA1 is the best hash option for out-of-the-box OpenLDAP
        # 'ldap_sha1'
        # Django's implementation of PBKDF2 SHA256 (default Django password
        # hasher, not supported by LDAP)
        'django_pbkdf2_sha256',
    ],
    'default': 'ldap_pbkdf2_sha256',
    # Use SHA1 if OpenLDAP doesn't ahve PBKDF2 module available/enabled
    # 'default': 'ldap_sha1',
    'deprecated': [
        # 'ldap_sha1',
        'django_pbkdf2_sha256',
    ],
    'ldap_pbkdf2_sha256__min_rounds': 100000,
    'django_pbkdf2_sha256__min_rounds': 100000,
}
