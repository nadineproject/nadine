import logging
import random
import string
import requests

import owncloud as NextCloudCLI

from django.dispatch import receiver

from .models import alerts

from .settings import *

logger = logging.getLogger(__name__)


def randomStringDigits(stringLength=8):
    # Generate a random string of letters and digits
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


@receiver(alerts.new_membership)
@receiver(new_membership)
def adding_nexcloud_user(sender, **kwargs):
    # Add new member on the nextcloud server
    _user = kwargs['user']
    _pass = NEXTCLOUD_USER_DEFAULT_PASSWORD or randomStringDigits()

    _admin = NEXTCLOUD_ADMIN
    _admin_key = NEXTCLOUD_PASSWORD

    _url = '%s://%s' % (('http', 'https')[NEXTCLOUD_USE_HTTPS is True], NEXTCLOUD_HOST)

    nc = NextCloudCLI.Client(_url, verify_certs=NEXTCLOUD_SSL_IS_SIGNED)
    _err = ['login', 'create_user', 'enable_user', 'add_user_to_group', 'set_user_attribute quota']
    try:
        nc.login(_admin, _admin_key)
        _err.pop(0)
        try:
            if NEXTCLOUD_USER_SEND_EMAIL_PASSWORD is True:
                nc.make_ocs_request('POST', nc.OCS_SERVICE_CLOUD, 'users',
                                    data={'email': _user.email, 'userid': _user.username}
                                    )
            else:
                nc.create_user(_user.username, _pass)
            _err.pop(0)
        except NextCloudCLI.OCSResponseError as e:
            if e.status_code == 102:
                _err.pop(0)
                nc.make_ocs_request('PUT', 'cloud/users', _user.username + '/enable')
            else:
                raise e
        _err.pop(0)
        if NEXTCLOUD_USER_GROUP is not None:
            nc.add_user_to_group(_user.username, NEXTCLOUD_USER_GROUP)
        _err.pop(0)
        if NEXTCLOUD_USER_QUOTA is not None:
            nc.set_user_attribute(_user.username, 'quota', NEXTCLOUD_USER_QUOTA)
        nc.logout()

    except NextCloudCLI.HTTPResponseError as e:
        logger.debug('adding_nexcloug_user: %s HTTP Error %d' % (_err[0], e.status_code))
    except requests.exceptions.ConnectionError as e:
        logger.debug('adding_nexcloug_user: %s Connection Error: %s' % (_err[0], e))
    except NextCloudCLI.OCSResponseError as e:
        logger.debug('adding_nexcloug_user: %s OCSResponse Error %d' % (_err[0], e.status_code))
    else:
        logger.debug('Adding user %s success' % _user.username)


@receiver(alerts.ending_membership)
@receiver(ending_membership)
def deactivating_nexcloud_user(sender, **kwargs):
    # Remove member on the nextcloud server
    _user = kwargs['user']

    _admin = NEXTCLOUD_ADMIN
    _admin_key = NEXTCLOUD_PASSWORD

    _url = ('http', 'https')[NEXTCLOUD_USE_HTTPS is True] + '://' + NEXTCLOUD_HOST

    nc = NextCloudCLI.Client(_url, verify_certs=NEXTCLOUD_SSL_IS_SIGNED)
    _err = ['login', 'deactivate_user']
    try:
        nc.login(_admin, _admin_key)
        _err.pop(0)
        nc.make_ocs_request('PUT', 'cloud/users', _user.username + '/disable')
        nc.logout()

    except NextCloudCLI.HTTPResponseError as e:
        logger.debug('removing_nexcloug_user: %s HTTP Error %d' % (_err[0], e.status_code))
    except requests.exceptions.ConnectionError as e:
        logger.debug('removing_nexcloug_user: %s Connection Error: %s' % (_err[0], e))
    except NextCloudCLI.OCSResponseError as e:
        logger.debug('removing_nexcloug_user: %s OCSResponse Error %d' % (_err[0], e.status_code))
    else:
        logger.debug('Removing user %s success' % _user.username)


@receiver(alerts.changing_membership_password)
@receiver(changing_membership_password)
def changing_nexcloud_user_password(sender, **kwargs):
    # Change user password on the nextcloud server
    _user = kwargs['user']
    _pass = kwargs['password']

    _admin = NEXTCLOUD_ADMIN
    _admin_key = NEXTCLOUD_PASSWORD

    _url = ('http', 'https')[NEXTCLOUD_USE_HTTPS is True] + '://' + NEXTCLOUD_HOST

    nc = NextCloudCLI.Client(_url, verify_certs=NEXTCLOUD_SSL_IS_SIGNED)
    _err = ['login', 'set_user_attribute password']
    try:
        nc.login(_admin, _admin_key)
        _err.pop(0)
        nc.set_user_attribute(_user.username, 'password', _pass)
        nc.logout()

    except NextCloudCLI.HTTPResponseError as e:
        logger.debug('changing_nexcloud_user_password: %s HTTP Error %d' % (_err[0], e.status_code))
    except requests.exceptions.ConnectionError as e:
        logger.debug('changing_nexcloud_user_password: %s Connection Error: %s' % (_err[0], e))
    except NextCloudCLI.OCSResponseError as e:
        logger.debug('changing_nexcloud_user_password: %s OCSResponse Error %d' % (_err[0], e.status_code))
    else:
        logger.debug('Changing user %s password success' % _user.username)
