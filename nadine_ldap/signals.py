from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete

from nadine.models import User, EmailAddress
from nadine_ldap.models import LDAPAccountStatus
from nadine_ldap.ldap import get_ldap_account_safely, update_ldap_account, delete_ldap_account

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    """
    Update user's LDAP account.
    """
    user = kwargs['instance']
    update_ldap_account(user, create=True)

@receiver(pre_delete, sender=User)
def user_pre_delete(**kwargs):
    """
    Delete users's LDAP account.
    """
    user = kwargs['instance']
    ldap_account = get_ldap_account_safely(user)
    if ldap_account:
        delete_ldap_account(ldap_account)

@receiver(post_save, sender=EmailAddress)
def email_address_post_save(**kwargs):
    """
    Update email address fields in user's LDAP account.
    Because email addresses are stored in a seperate model linked to User by a
    ForeignKey, we need to independently listen for changes.
    TODO: Gets called multiple times when a user account is saved (once for each
          email address).
    """
    email_address = kwargs['instance']
    update_ldap_account(email_address.user)

@receiver(post_delete, sender=EmailAddress)
def email_address_post_delete(**kwargs):
    """
    Delete email addresses from user's LDAP account.
    Because email addresses are stored in a seperate model linked to User by a
    ForeignKey, we need to independently listen for changes.
    TODO: Gets called multiple times when a user account is saved/deleted (once
          for each email address).
    """
    email_address = kwargs['instance']
    update_ldap_account(email_address.user)