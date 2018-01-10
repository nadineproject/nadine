from __future__ import unicode_literals

from django.db.utils import Error as DBError

from models import LDAPPosixUser, LDAPAccountStatus

def update_or_create_ldap_account(user):
    """
    Attempt to create a user account in LDAP. Log any errors that occur.
    """
    try:
        ldap_status, created = LDAPAccountStatus.objects.get_or_create(user=user)
        email_addresses = map((lambda address: address.email), user.emailaddress_set.all())
        ldap_posix_user, created = LDAPPosixUser.objects.update_or_create(
            nadine_id=str(ldap_status.pk),
            defaults={
                'common_name': user.username,
                'password': user.password,
                'last_name': user.username,
                'email': email_addresses,
            },
        )
        return clear_ldap_error(user, ldap_posix_user.dn)

    except DBError as ldap_error:
        # Log error and let Django continue as normal.
        return log_ldap_error(user, ldap_error)


def log_ldap_error(user, ldap_error):
    """
    Something went wrong writing to LDAP. Record the problem in Django database
    in a record associated with the user's account.
    """
    ldap_status, create = LDAPAccountStatus.objects.update_or_create(
        user=user,
        defaults={
            'synchronized': False,
            'ldap_error_message': str(ldap_error)
        }
    )
    return ldap_status


def clear_ldap_error(user, ldap_user_dn=None):
    """
    Clears any errors recorded in user's LDAPAccountStatus object.
    Optionally, provide a LDAP dn to be recorded if one exists.
    """
    ldap_status, created = LDAPAccountStatus.objects.update_or_create(
        user=user,
        defaults={
            'ldap_dn': ldap_user_dn if ldap_user_dn is not None else '',
            'synchronized': True,
            'ldap_error_message': ''
        }
    )
    return ldap_status
