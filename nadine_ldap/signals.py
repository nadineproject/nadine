from __future__ import unicode_literals

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.db.utils import Error as DBError

from models import LDAPPosixUser, LDAPAccountStatus

# @receiver(pre_save, sender=User)
# def user_pre_save(**kwargs):
#     pass

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    user = kwargs['instance']
    try:
        LDAPPosixUser.objects.update_or_create(
            username=user.username,
            full_name=user.username,
            last_name=user.username,
            password=user.password
        )
    except DBError as ldap_error:
        """
        Something went wrong writing to LDAP. We don't want to interrupt the
        user. Instead we record the problem in Nadine's database in a record
        associated with the user's account.
        """
        LDAPAccountStatus.objects.update_or_create(
            user=user,
            defaults={
                'has_error': True,
                'last_error': str(ldap_error)
            }
        )

@receiver(post_save, sender=LDAPPosixUser)
def ldap_posix_user_post_save(**kwargs):
    ldap_posix_user = kwargs['instance']
    user = User.objects.get(username=ldap_posix_user.username)
    LDAPAccountStatus.objects.update_or_create(
        user=user,
        defaults={
            'ldap_dn': ldap_posix_user.dn,
            'has_error': False,
            'last_error': ''
        }
    )