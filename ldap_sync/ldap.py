from __future__ import unicode_literals

from django.db.utils import Error as DBError

from ldap_sync.models import LDAPPosixUser, LDAPAccountStatus

def get_ldap_account_safely(user):
    """
    Safely check if user has an LDAPAccountStatus record.
    If exists, return it, otherwise returns None.
    """
    if hasattr(user, 'ldapaccountstatus'):
        return user.ldapaccountstatus


def get_or_create_ldap_account(user):
    ldap_status, _ = LDAPAccountStatus.objects.get_or_create(user=user)
    return ldap_status


def update_ldap_account(user, create=False):
    """
    Attempt to create a user account in LDAP. Log any errors that occur.
    """
    ldap_status = None
    if create:
        ldap_status = get_or_create_ldap_account(user)
    else:
        ldap_status = get_ldap_account_safely(user)

    if not ldap_status:
        return

    user = ldap_status.user
    email_addresses = [address.email for address in user.emailaddress_set.all()]
    try:
        ldap_posix_user, _ = LDAPPosixUser.objects.update_or_create(
            nadine_id=ldap_status.ldap_uid,
            defaults={
                'common_name': user.username,
                'password': user.password,
                'last_name': user.username,
                'email': email_addresses,
            },
        )
        ldap_status.ldap_dn = ldap_posix_user.dn
        clear_ldap_error(ldap_status)

    except DBError as error:
        # Log error and let Django continue as normal.
        log_ldap_error(ldap_status, error)


def delete_ldap_account(ldap_status):
    try:
        ldap_posix_user = LDAPPosixUser.objects.get(nadine_id=ldap_status.ldap_uid)
        ldap_posix_user.delete()
        ldap_status.delete()

    except LDAPPosixUser.DoesNotExist:
        # LDAP account has been deleted so it's ok to clean up the ldap_status
        # object.
        ldap_status.delete()

    except DBError as error:
        # In the case that we can't connect and/or delete from LDAP, hold off on
        # removing our reference of the object for cron to try clean up at a
        # later date.
        log_ldap_error(ldap_status, error)



def log_ldap_error(ldap_status, error):
    """
    Something went wrong writing to LDAP. Record the problem in Django database
    in a record associated with the user's account.
    """
    ldap_status.synchronized = False
    ldap_status.ldap_error_message = str(error)
    ldap_status.save()


def clear_ldap_error(ldap_status):
    """
    Clears any errors recorded in user's LDAPAccountStatus object.
    Optionally, provide a LDAP dn to be recorded if one exists.
    """
    ldap_status.synchronized = True
    ldap_status.ldap_error_message = ''
    ldap_status.save()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
