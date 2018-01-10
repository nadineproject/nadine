from django.db.utils import Error as DBError

from models import LDAPPosixUser, LDAPAccountStatus

def update_or_create_ldap_account(user):
    """
    Attempt to create a user account in LDAP. Log any errors that occur.
    """
    try:
        ldap_status, created = LDAPAccountStatus.objects.get_or_create(user=user)
        LDAPPosixUser.objects.update_or_create(
            nadine_id=str(ldap_status.pk),
            #TODO: email=[..., ...]
            defaults={
                'common_name': user.username,
                'password': user.password,
                'last_name': user.username,
            },
        )
    except DBError as ldap_error:
        # Log error and let Django continue as normal.
        log_ldap_error(user, ldap_error)

def log_ldap_error(user, ldap_error):
    """
    Something went wrong writing to LDAP. Record the problem in Django database
    in a record associated with the user's account.
    """
    LDAPAccountStatus.objects.update_or_create(
        user=user,
        defaults={
            'synchronized': False,
            'ldap_error_message': str(ldap_error)
        }
    )

def clear_ldap_error(user, ldap_user_dn=None):
    """
    Clears any errors recorded in user's LDAPAccountStatus object.
    Optionally, provide a LDAP dn to be recorded if one exists.
    """
    LDAPAccountStatus.objects.update_or_create(
        user=user,
        defaults={
            'ldap_dn': ldap_user_dn if ldap_user_dn is not None else '',
            'synchronized': True,
            'ldap_error_message': ''
        }
    )
