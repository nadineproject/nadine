from __future__ import unicode_literals

from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from models import LDAPPosixUser, UsersLDAPAccount

# @receiver(pre_save, sender=User)
# def user_pre_save(**kwargs):
#     pass

@receiver(post_save, sender=User)
def user_post_save(**kwargs):
    user = kwargs['instance']
    LDAPPosixUser.objects.update_or_create(
        username=user.username,
        full_name=user.username,
        last_name=user.username
    )

@receiver(pre_save, sender=LDAPPosixUser)
def ldap_posix_user_pre_save(**kwargs):
    try:
        ldap_posix_user = kwargs['instance']
        user = User.objects.get(username=ldap_posix_user.username)
        # LDAP write succeeded! Clear any recorded LDAP errors.
        # TODO: Verify username change correctly propagates to ldap_dn value.
        usersLDAPAccount = UsersLDAPAccount.objects.update_or_create(
            user=user,
            defaults={
                'ldap_dn': ldap_posix_user.dn,
                'exists_in_ldap': True,
                'has_error': False,
                'last_error': ''
            }
        )
    except User.DoesNotExist:
        # TODO: Something went very wrong, log this.
        pass