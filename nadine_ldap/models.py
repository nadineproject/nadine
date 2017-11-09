from __future__ import unicode_literals

from django.conf import settings

from ldapdb.models.fields import (CharField, ListField, IntegerField)
import ldapdb.models

class LDAPUser(ldapdb.models.Model):
    """
    Class for representing an LDAP user entry.
    """
    # LDAP meta-data
    base_dn = settings.NADINE_LDAP_USER_BASE_DN
    object_classes = ['top', 'posixAccount', 'inetOrgPerson'] #'shadowAccount', 

    # inetOrgPerson
    first_name = CharField(db_column='givenName', verbose_name="Prime name")
    last_name = CharField("Final name", db_column='sn')
    full_name = CharField(db_column='cn')
    email = ListField(db_column='mail')

    # posixAccount
    uid = IntegerField(db_column='uidNumber', unique=True)
    group = IntegerField(db_column='gidNumber')
    home_directory = CharField(db_column='homeDirectory')
    login_shell = CharField(db_column='loginShell', default='/bin/bash')
    username = CharField(db_column='uid', primary_key=True)
    password = CharField(db_column='userPassword')

    def __str__(self):
        return self.username

    def __unicode__(self):
        return self.full_name


class LDAPGroup(ldapdb.models.Model):
    """
    Class for representing an LDAP group entry.
    """
    # LDAP meta-data
    base_dn = settings.NADINE_LDAP_GROUP_BASE_DN
    object_classes = ['posixGroup']

    # posixGroup attributes
    gid = IntegerField(db_column='gidNumber', unique=True)
    name = CharField(db_column='cn', max_length=200, primary_key=True)
    usernames = ListField(db_column='memberUid')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name