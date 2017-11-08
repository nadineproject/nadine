from .base import *

import ldap
from django_auth_ldap.config import LDAPSearch

# Application definition
#
INSTALLED_APPS += [
    'nadine_ldap',
]

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
    # Match against uid (alias: 'User Name') or mail (alias: 'Email')
    # attribute. The 'mail' attribute can contain multiple values in LDAP but
    # they must be unique.
    "(|(uid=%(user)s)(mail=%(user)s))"
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
