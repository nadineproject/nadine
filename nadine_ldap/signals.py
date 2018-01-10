from __future__ import unicode_literals

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save

from models import LDAPPosixUser, LDAPAccountStatus
from ldap import update_or_create_ldap_account, clear_ldap_error

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    user = kwargs['instance']
    update_or_create_ldap_account(user)

@receiver(post_save, sender=LDAPPosixUser)
def ldap_posix_user_post_save(**kwargs):
    ldap_posix_user = kwargs['instance']
    ldap_status = LDAPAccountStatus.objects.get(pk=ldap_posix_user.nadine_id)
    clear_ldap_error(ldap_status.user, ldap_posix_user.dn)
