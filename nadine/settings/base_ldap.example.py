from __future__ import unicode_literals

from .base import *

import ldap
from django_auth_ldap.config import LDAPSearch


# Application definition
#
INSTALLED_APPS += [
    'nadine_ldap.apps.NadineLdapConfig',
]

# Overriding Django Auth's hashers with those from PassLib
django_contrib_auth_index = INSTALLED_APPS.index('django.contrib.auth')
INSTALLED_APPS.insert(django_contrib_auth_index + 1, 'passlib.ext.django')


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
NADINE_LDAP_USER_BASE_DN = "ou=users,dc=tnightingale,dc=com"
NADINE_LDAP_GROUP_BASE_DN = "ou=groups,dc=tnightingale,dc=com"
NADINE_LDAP_MEMBERS_GROUP_CN = "members"
NADINE_LDAP_USER_HOME_DIR_TEMPLATE = "/home/{}"


# LDAP Auth
# https://django-auth-ldap.readthedocs.io/en/1.2.x/authentication.html#server-config
#
AUTHENTICATION_BACKENDS += (
    'nadine_ldap.auth.NadineLDAPBackend',
)
AUTH_LDAP_BIND_DN = "cn=admin,dc=312main,dc=ca"
AUTH_LDAP_BIND_PASSWORD = ""
# Search query for a user.
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    # Look under 'users' organizational unit (ou)
    "ou=users,dc=312main,dc=ca",
    ldap.SCOPE_SUBTREE,
    # Match against cn (alias: 'Common Name') or mail (alias: 'Email')
    # attribute. The 'mail' attribute can contain multiple values in LDAP but
    # they must be unique.
    "(|(cn=%(user)s)(mail=%(user)s))"
)
# TODO: These allow us to change properties on Django user object based on
#       their LDAP group membership.
# from django_auth_ldap.config import LDAPGroupQuery, PosixGroupType
# AUTH_LDAP_USER_FLAGS_BY_GROUP = {
#     "is_active": "cn=members,ou=groups,dc=312main,dc=ca",
#     "is_staff": LDAPGroupQuery("cn=users,ou=groups,dc=312main,dc=ca")
# }
# TODO: The below configuration is only required if we search on any group
#       objects or group membership.
# AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
#     "ou=groups,dc=312main,dc=ca",
#     ldap.SCOPE_SUBTREE,
#     "(objectClass=posixGroup)"
# )
# AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")


# PassLib provides LDAP-compatible password hashing, hash formatting and
# authentication.
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
    'ldap_pbkdf2_sha256__min_rounds': 36000,
    'django_pbkdf2_sha256__min_rounds': 36000,
}