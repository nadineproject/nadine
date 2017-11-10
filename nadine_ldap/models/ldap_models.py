from __future__ import unicode_literals

from django.conf import settings
from django.db import models

from ldapdb.models.fields import (CharField, ListField, IntegerField)
from ldapdb.models import Model as LDAPModel


def _next_posix_id(prev_id=None, starting_id=1000):
    return prev_id if prev_id is not None else starting_id

class LDAPPosixObject(object):
    """
    Mixin to handle some of the uglyness when it comes to creating new
    objects. LDAP doesn't autoincrement ids so we need to do a manual lookup
    and increment.
    """

    def ensure_id(self):
        """
        Fetching last id so we can safely set a new one.
        This is not ideal but apparently (based on a brief internet search)
        it's the only way to increment posix id with LDAP.
        """
        if not hasattr(self, 'ID_FIELD_NAME'):
            raise Exception("LDAPPosixObjects must declare an ID_FIELD_NAME property")
        if getattr(self, self.ID_FIELD_NAME) is None:
            # In theory Django does its best to prevent you from accessing a
            # model's manager from inside the model:
            # https://docs.djangoproject.com/en/dev/topics/db/queries/#retrieving-objects
            # Not sure if that same rule applies to mixins but it probably does.
            last_obj = self.__class__.objects.order_by(self.ID_FIELD_NAME).first()
            obj_id = _next_posix_id(getattr(last_obj, self.ID_FIELD_NAME))
            setattr(self, self.ID_FIELD_NAME, obj_id)

    def save(self, *args, **kwargs):
        """
        Overriding to ensure we have a safe ID when creating the object.
        """
        self.ensure_id()
        return super(LDAPPosixObject, self).save(*args, **kwargs)


class LDAPPosixGroupManager(models.Manager):
    pass


class LDAPPosixGroup(LDAPPosixObject, LDAPModel):
    """
    Class for representing an LDAP group entry.
    """

    objects = LDAPPosixGroupManager()
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


class LDAPPosixUserManager(models.Manager):
    pass


class LDAPPosixUser(LDAPPosixObject, LDAPModel):
    """
    Class for representing an LDAP user entry.
    """
    ID_FIELD_NAME = 'uid'

    objects = LDAPPosixUserManager()

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
            members_group, created = LDAPPosixGroup.objects.get_or_create(
                name=settings.NADINE_LDAP_MEMBERS_GROUP_CN
            )
            self.group = members_group.gid

    def ensure_home_directory(self):
        """
        If no home_directory is set then LDAP complains, we can auto-populate.
        """
        if not self.home_directory:
            self.home_directory = self.HOME_DIR_TEMPLATE.format(
                self.username if self.username is not None else self.uid
            )

    def save(self, *args, **kwargs):
        self.ensure_gid()
        self.ensure_home_directory()
        return super(LDAPPosixUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.username

    def __unicode__(self):
        return self.full_name