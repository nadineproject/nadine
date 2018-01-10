from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models.signals import post_save

from nadine.models import User, EmailAddress
from nadine_ldap.models import LDAPPosixUser, LDAPAccountStatus
from nadine_ldap.ldap import update_or_create_ldap_account, clear_ldap_error

@receiver(post_save, sender=EmailAddress)
def email_address_post_save(**kwargs):
    """
    Update email address fields in user's LDAP account.
    TODO: Gets called multiple times when a user account is saved (once for each
          email address).
    """
    email_address = kwargs['instance']
    update_or_create_ldap_account(email_address.user)

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    """
    Update user's LDAP account.
    """
    user = kwargs['instance']
    update_or_create_ldap_account(user)

@receiver(post_save, sender=LDAPPosixUser)
def ldap_posix_user_post_save(**kwargs):
    """
    User's LDAP account was successfully updated, we can safely clear any
    outstanding errors.
    """
    ldap_posix_user = kwargs['instance']
    ldap_status = LDAPAccountStatus.objects.get(pk=ldap_posix_user.nadine_id)
    clear_ldap_error(ldap_status.user, ldap_posix_user.dn)
