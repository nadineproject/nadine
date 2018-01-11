from __future__ import unicode_literals

from django.conf import settings
from django.db import models

from ldapdb.models.fields import (CharField, ListField, IntegerField)
from ldapdb.models import Model as LDAPModel


class LDAPPosixGroupManager(models.Manager):
    pass


class LDAPPosixGroup(LDAPModel):
    """
    Class for representing an LDAP group entry.
    """

    objects = LDAPPosixGroupManager()
    # LDAP meta-data
    base_dn = settings.NADINE_LDAP_GROUP_BASE_DN
    object_classes = ['posixGroup']

    # posixGroup attributes
    gid = IntegerField(db_column='gidNumber', default=500)
    name = CharField(db_column='cn', max_length=200, primary_key=True)
    usernames = ListField(db_column='memberUid')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class LDAPPosixUserManager(models.Manager):
    pass


class LDAPPosixUser(LDAPModel):
    """
    Class for representing an LDAP user entry.
    """

    objects = LDAPPosixUserManager()

    # LDAP meta-data
    base_dn = settings.NADINE_LDAP_USER_BASE_DN
    object_classes = ['top', 'posixAccount', 'inetOrgPerson']

    # inetOrgPerson
    first_name = CharField(db_column='givenName', verbose_name="Prime name")
    last_name = CharField("Final name", db_column='sn')
    common_name = CharField(db_column='cn')
    email = ListField(db_column='mail')

    # posixAccount
    uid = IntegerField(db_column='uidNumber', default=1000)
    group = IntegerField(db_column='gidNumber')
    home_directory = CharField(db_column='homeDirectory')
    login_shell = CharField(db_column='loginShell', default='/bin/bash')
    nadine_id = CharField(db_column='uid', primary_key=True)
    password = CharField(db_column='userPassword')

    if hasattr(settings, 'NADINE_LDAP_USER_HOME_DIR_TEMPLATE'):
        HOME_DIR_TEMPLATE = settings.NADINE_LDAP_USER_HOME_DIR_TEMPLATE
    else:
        HOME_DIR_TEMPLATE = "/home/{}"

    def ensure_gid(self):
        """
        If no group is set then perform a get_or_create() for default members
        group.
        """
        if self.group is None:
            members_group, _ = LDAPPosixGroup.objects.get_or_create(
                name=settings.NADINE_LDAP_MEMBERS_GROUP_CN
            )
            self.group = members_group.gid

    def ensure_home_directory(self):
        """
        If no home_directory is set then LDAP complains, we can auto-populate.
        """
        if not self.home_directory:
            self.home_directory = self.HOME_DIR_TEMPLATE.format(self.uid)

    def save(self, *args, **kwargs):
        self.ensure_gid()
        self.ensure_home_directory()
        return super(LDAPPosixUser, self).save(*args, **kwargs)

    def __str__(self):
        return "{}:{}".format(self.nadine_id, self.common_name)

    def __unicode__(self):
        return self.full_name