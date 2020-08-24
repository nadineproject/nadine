import logging
import random
import string
import requests

from rocketchat_API.rocketchat import RocketChat
from rocketchat_API.APIExceptions.RocketExceptions import RocketConnectionException, RocketAuthenticationException, \
    RocketException, RocketMissingParamException

from django.dispatch import receiver

from .models import alerts

from .settings import *

logger = logging.getLogger(__name__)


def randomStringDigits(stringLength=8):
    # Generate a random string of letters and digits
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def checkSuccess(user):
    # Check success of api request
    if user.get("success") is False:
        raise RocketException(f'{user.get("error")}')


@receiver(alerts.new_membership)
@receiver(new_membership)
def adding_rocketchat_user(sender, **kwargs):
    # Add new member on the rocketchat server
    _user = kwargs['user']
    _pass = ROCKETCHAT_USER_DEFAULT_PASSWORD or randomStringDigits()

    _admin = ROCKETCHT_ADMIN
    _admin_key = ROCKETCHAT_SECRET

    _url = f"{('http', 'https')[ROCKETCHAT_USE_HTTPS is True]}://{ROCKETCHAT_HOST}"

    _err = ['login', 'user_info', 'create_user', 'add_to_group']
    try:
        rocket = RocketChat(_admin, _admin_key, server_url=_url, ssl_verify=ROCKETCHAT_SSL_IS_SIGNED)
        _err.pop(0)
        user = rocket.users_info(username=_user.username).json()
        _err.pop(0)
        if user.get("success") is False:
            user = rocket.users_create(_user.email, _user.username, _pass, _user.username,
                                       sendWelcomeEmail=ROCKETCHAT_SEND_WELCOME_MAIL,
                                       requirePasswordChange=ROCKETCHAT_REQUIRE_CHANGE_PASS,
                                       verified=ROCKETCHAT_VERIFIED_USER).json()
            checkSuccess(user)
        _err.pop(0)
        if ROCKETCHAT_USER_GROUP is not None:
            for group in ROCKETCHAT_USER_GROUP:
                res = rocket.groups_info(room_name=group).json()
                checkSuccess(res)
                res = rocket.groups_invite(res.get("group").get("_id"), user.get("user").get("_id")).json()
                checkSuccess(res)
        _err.pop(0)
    except RocketAuthenticationException as e:
        logger.debug(f'adding_rocketchat_user: {_err[0]} Rocket Authentication Error: {e.__str__()}')
    except RocketConnectionException as e:
        logger.debug(f'adding_rocketchat_user: {_err[0]} Rocket Connection Error: {e.__str__()}')
    except RocketMissingParamException as e:
        logger.debug(f'adding_password: {_err[0]} Rocket Missing Param Error {e.__str__()}')
    except RocketException as e:
        logger.debug(f'adding_rocketchat_user: {_err[0]} Rocket Error: {e.__str__()}')
    except requests.exceptions.ConnectionError as e:
        logger.debug(f'adding_rocketchat_user: {_err[0]} Connection Error: {e.__str__()}')
    else:
        logger.debug(f'Adding user {_user.username} success')


@receiver(alerts.ending_membership)
@receiver(ending_membership)
def deactivating_rocketchat_user(sender, **kwargs):
    # Remove subscribed group on the rocketchat server
    _user = kwargs['user']

    _admin = ROCKETCHT_ADMIN
    _admin_key = ROCKETCHAT_SECRET

    _url = f"{('http', 'https')[ROCKETCHAT_USE_HTTPS is True]}://{ROCKETCHAT_HOST}"

    _err = ['login', 'user_info', 'remove_on_group']
    try:
        rocket = RocketChat(_admin, _admin_key, server_url=_url, ssl_verify=ROCKETCHAT_SSL_IS_SIGNED)
        _err.pop(0)
        user = rocket.users_info(username=_user.username).json()
        checkSuccess(user)
        _err.pop(0)
        if ROCKETCHAT_USER_GROUP is not None:
            for group in ROCKETCHAT_USER_GROUP:
                res = rocket.groups_info(room_name=group).json()
                checkSuccess(res)
                res = rocket.groups_kick(res.get("group").get("_id"), user.get("user").get("_id")).json()
                checkSuccess(res)
        _err.pop(0)
    except RocketAuthenticationException as e:
        logger.debug(f'removing_rocketchat_user: {_err[0]} Rocket Authentication Error: {e.__str__()}')
    except RocketConnectionException as e:
        logger.debug(f'removing_rocketchat_user: {_err[0]} Rocket Connection Error: {e.__str__()}')
    except RocketMissingParamException as e:
        logger.debug(f'removing_password: {_err[0]} Rocket Missing Param Error {e.__str__()}')
    except RocketException as e:
        logger.debug(f'removing_rocketchat_user: {_err[0]} Rocket Error: {e.__str__()}')
    except requests.exceptions.ConnectionError as e:
        logger.debug(f'removing_rocketchat_user: {_err[0]} Connection Error: {e.__str__()}')
    else:
        logger.debug(f'Removing user {_user.username} success')


@receiver(alerts.changing_membership_password)
@receiver(changing_membership_password)
def changing_rocketchat_user_password(sender, **kwargs):
    # Change user password on the rocketchat server
    _user = kwargs['user']
    _pass = kwargs['password']

    _admin = ROCKETCHT_ADMIN
    _admin_key = ROCKETCHAT_SECRET

    _url = f"{('http', 'https')[ROCKETCHAT_USE_HTTPS is True]}://{ROCKETCHAT_HOST}"

    _err = ['login', 'user_info', 'update_password']
    try:
        rocket = RocketChat(_admin, _admin_key, server_url=_url, ssl_verify=ROCKETCHAT_SSL_IS_SIGNED)
        _err.pop(0)
        user = rocket.users_info(username=_user.username).json()
        checkSuccess(user)
        _err.pop(0)
        user = rocket.users_update(user.get("user").get("_id"), password=_pass).json()
        checkSuccess(user)
        _err.pop(0)
    except RocketAuthenticationException as e:
        logger.debug(f'changing_rocketchat_password: {_err[0]} Rocket Authentication Error: {e.__str__()}')
    except RocketConnectionException as e:
        logger.debug(f'changing_rocketchat_password: {_err[0]} Rocket Connection Error: {e.__str__()}')
    except RocketMissingParamException as e:
        logger.debug(f'changing_rocketchat_password: {_err[0]} Rocket Missing Param Error {e.__str__()}')
    except RocketException as e:
        logger.debug(f'changing_rocketchat_password: {_err[0]} Rocket Error {e.__str__()}')
    except requests.exceptions.ConnectionError as e:
        logger.debug(f'changing_rocketchat_password: {_err[0]} Connection Error: {e.__str__()}')
    else:
        logger.debug(f'Changing user {_user.username} password success')
