from .base import *

import ldap
from django_auth_ldap.config import LDAPSearch, LDAPGroupQuery, PosixGroupType

# Database
# https://github.com/django-ldapdb/django-ldapdb#using-django-ldapdb
#
DATABASES['ldap'] = {
    'ENGINE': 'ldapdb.backends.ldap',
    'NAME': 'ldap://localhost',
    'USER': 'cn=admin,dc=tnightingale,dc=com',
    'PASSWORD': 'cleo31',
}
DATABASE_ROUTERS = ['ldapdb.router.Router']

# Application definition
#
INSTALLED_APPS += [
    'nadine_ldap',
]

# LDAP Auth
# https://django-auth-ldap.readthedocs.io/en/1.2.x/authentication.html#server-config
#
AUTHENTICATION_BACKENDS += (
    'django_auth_ldap.backend.LDAPBackend',
)

AUTH_LDAP_BIND_DN = "cn=admin,dc=tnightingale,dc=com"
AUTH_LDAP_BIND_PASSWORD = "cleo31"

# Search query for a user.
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    # Look under 'users' organizational unit (ou)
    "ou=users,dc=tnightingale,dc=com",
    ldap.SCOPE_SUBTREE,
    # Match against the uid (alias: 'User Name') attribute
    "(uid=%(user)s)"
    # TODO: Need to match against mail (alias: 'Email') attribute, this can
    #       contain multiple values in LDAP. The below check will end up
    #       creating a Django user for each value which is not what we want.
    #       Ideally we would be able to resolve the returned LDAP object to an
    #       existing field via a different (unique) attribute such as uid.
    # UPDATE:
    #       This can be done with a custom LDAPBackend that overrides
    #       get_or_create_user() (https://django-auth-ldap.readthedocs.io/en/1.2.x/reference.html#django_auth_ldap.backend.LDAPBackend.get_or_create_user).
    # "(mail=%(user)s)"
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=tnightingale,dc=com",
    ldap.SCOPE_SUBTREE,
    "(objectClass=posixGroup)"
)

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": "cn=users,ou=groups,dc=tnightingale,dc=com",
    "is_staff": LDAPGroupQuery("cn=users,ou=groups,dc=tnightingale,dc=com")
}

AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")
