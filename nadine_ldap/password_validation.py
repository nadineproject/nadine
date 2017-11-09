from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from ldapdb.backends.ldap.base import LdapDatabase

import models

class LDAPSyncValidator(object):
    """
    This isn't actually a password validator. Instead we're (ab)using Django's
    password validator hooks as a way of catching user passwords in plain text
    to send to LDAP.

    Not exactly pretty but it seems reliable. The alternative is to create a new
    User model and override set_password(). This would work but requires
    significant refactoring of the existing Nadine codebase: all references to
    django.contrib.auth.models.User would need to be replaced (ideally with
    get_user_model() & settings.DJANGO_AUTH_USER).

    Changing the user model is easy to do with a fresh database but very
    difficult and highly discouraged if you already have a database. In the
    event that Office Nomads decide they want LDAP, we would be in trouble.

    See below for more info:
    https://docs.djangoproject.com/en/1.11/topics/auth/customizing/#changing-to-a-custom-user-model-mid-project
    https://docs.djangoproject.com/en/1.11/topics/auth/customizing/#reusable-apps-and-auth-user-model
    """
    def validate(self, password, user=None):
        # Called before user is saved to DB
        # Able to bail if LDAP fails
        # Might prematurely create LDAP account (eg: user save fails).
        self.set_or_update_ldap_user_password(user, password)
        pass

    def password_changed(self, password, user=None):
        # Always called after user is saved to DB
        # Not called if user save fails
        # Can't bail if LDAP fails.
        # self.set_or_update_ldap_user_password(user, password)
        pass

    def set_or_update_ldap_user_password(self, user, password):
        if (user is None):
            # Nothing we can do here (except maybe log something?)
            return
        try:
            # Get a group's gid; posixAccount requires user belong to a group
            members_dn = "cn=members,ou=groups,dc=tnightingale,dc=com" # settings.NADINE_LDAP_MEMBERS_GROUP_DN
            # TODO: we should probably get_or_create() this
            members = models.LDAPGroup.objects.get(dn=members_dn)
            gid = members.gid

            # TODO: Move this into a helper LDAPUserManager.get_or_create()
            try:
                ldap_user = models.LDAPUser.objects.get(username=user.username)
            except models.LDAPUser.DoesNotExist:
                # Fetching last uid so we can safely set a new one.
                # This is not ideal but apparently (based on a brief internet
                # search) it's the only way to increment uid with LDAP.
                lastUser = models.LDAPUser.objects.order_by('uid').first()
                if (lastUser is not None):
                    uid = lastUser.uid + 1
                else:
                    uid = 1000 # settings.NADINE_LDAP_USER_STARTING_UID

                # Finally, we can create a user.
                ldap_user = models.LDAPUser.objects.create(
                    uid=uid,
                    group=gid,
                    home_directory="/home/{}".format(user.username), # settings.NADINE_LDAP_USER_HOME_DIR_TEMPLATE
                    full_name=user.username,
                    last_name=user.username,
                    username=user.username
                )
            # End LDAPUserManager.get_or_create()

            ldap_user.full_name = user.username
            ldap_user.password = password
            ldap_user.save()

        except Exception as e:
            raise ValidationError("There was a problem communicating with LDAP")
            # TODO: We either, raise django.core.exceptions.ValidationError
            #       (can't set/update user password), or we log and fail
            #       silently (user account is created *only* in Django)

    def get_help_text(self):
        return _("Your password will also be added to LDAP.")