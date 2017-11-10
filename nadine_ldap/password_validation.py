from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from ldapdb.backends.ldap.base import LdapDatabase
from ldap import LDAPError

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
        pass

    def password_changed(self, password, user=None):
        """
        Always called after user is saved to DB
        Not called if user save fails
        Can't bail if LDAP fails.
        """
        set_password(user, password)

    def get_help_text(self):
        """
        Provides help text for Django Auth's password form.
        """
        return _("Your password will also be added to LDAP.")

def set_password(user, password):
    """
    Set the plain-text password onto the LDAP representation of the user
    account.
    """
    if user is None:
        # Nothing we can do here (except maybe log something?)
        return

    try:
        ldap_user, created = models.LDAPPosixUser.objects.get_or_create(
            username=user.username,
            defaults={
                # Adding dummy values here
                'full_name': user.username,
                'last_name': user.username,
                'password': password
            }
        )
        if not created:
            ldap_user.password = password
            ldap_user.save()
    # TODO: ldap package produces a whole variety of exceptions, need to see if there's a better method of 
    except LDAPError as e:
        # Record failure in database.
        usersLDAPAccount = models.UsersLDAPAccount.objects.update_or_create(
            user=user,
            defaults={
                'has_error': True,
                'last_error': str(e)
            }
        )
        # TODO: We should log an error.
