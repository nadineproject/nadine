import logging
import requests

from django.dispatch import receiver

from .models import alerts

from .settings import *

from .models.elocky_cred import ElockyCred

logger = logging.getLogger(__name__)


@receiver(alerts.new_membership)
@receiver(new_membership)
def adding_elocky_user(sender, **kwargs):
    _user = kwargs['user']

    _cli_id = ELOCKY_API_CLIENT_ID
    _cli_pass = ELOCKY_API_CLIENT_SECRET
    _admin = ELOCKY_USERNAME
    _admin_key = ELOCKY_PASSWORD

    _err = ['login', 'sync_db', 'found_user_exist', 'new_access', 'add_user_in_db']
    try:
        url_login = 'https://www.elocky.com/oauth/v2/token'
        data_login = {'client_id': _cli_id, 'client_secret': _cli_pass, 'grant_type': 'password',
                      'username': _admin, 'password': _admin_key}
        response = requests.post(url_login, json=data_login)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)
        access_token = response.json().get('access_token')
        hed = {'Authorization': f'Bearer {access_token}'}
        _err.pop(0)
        ElockyCred.sync_elocky_invite(header=hed)
        _err.pop(0)
        elocky_user = bool(ElockyCred.objects.filter(username__exact=_user.username).exists())
        if elocky_user is True:
            raise Exception(f"Elocky username '{_user.username}' found in db/API")
        _err.pop(0)
        url_new_access = 'https://www.elocky.com/webservice/access/new.json'
        data_new_access = {'board': 2222, 'typeAccess': 4, 'nameAccess': _user.username}
        response = requests.post(url_new_access, json=data_new_access, headers=hed)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)
        _err.pop(0)
        elocky_id = response.json().get('id')
        num_access = response.json().get('num_access')
        code_access = response.json().get('code_access')
        ElockyCred.objects.create(username=_user.username, elocky_id=elocky_id, num_access=num_access,
                                  code_access=code_access)
    except requests.exceptions.HTTPError as e:
        logger.debug(f'adding_elocky_user: {_err[0]} Connection Error: {e.__str__()}')
    except requests.exceptions.ConnectionError as e:
        logger.debug(f'adding_elocky_user: {_err[0]} Connection Error: {e.__str__()}')
    except Exception as e:
        logger.debug(f'adding_elocky_user: {_err[0]} Error: {e.__str__()}')
    else:
        logger.debug(f'Adding user {_user.username} success')


@receiver(alerts.ending_membership)
@receiver(ending_membership)
def remove_elocky_user(sender, **kwargs):
    _user = kwargs['user']

    _cli_id = ELOCKY_API_CLIENT_ID
    _cli_pass = ELOCKY_API_CLIENT_SECRET
    _admin = ELOCKY_USERNAME
    _admin_key = ELOCKY_PASSWORD

    _err = ['login', 'sync_db', 'find_user_on_db', 'remove_user']
    try:
        url_login = 'https://www.elocky.com/oauth/v2/token'
        data_login = {'client_id': _cli_id, 'client_secret': _cli_pass, 'grant_type': 'password',
                      'username': _admin, 'password': _admin_key}
        response = requests.post(url_login, json=data_login)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)
        access_token = response.json().get('access_token')
        hed = {'Authorization': f'Bearer {access_token}'}
        _err.pop(0)
        ElockyCred.sync_elocky_invite(header=hed)
        _err.pop(0)
        elocky_user_l = ElockyCred.objects.filter(username__exact=_user.username).all()
        if elocky_user_l is None:
            raise Exception(f"Don't found elocky username '{_user.username}' in db/API")
        _err.pop(0)
        for elocky_user in elocky_user_l:
            url_remove_access = f'https://www.elocky.com/webservice/access/delete/{elocky_user.elocky_id}.json'
            response = requests.delete(url_remove_access, headers=hed)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            elocky_user.delete()
    except requests.exceptions.ConnectionError as e:
        logger.debug(f'removing_elocky_user: {_err[0]} Connection Error: {e.__str__()}')
    except requests.exceptions.HTTPError as e:
        logger.debug(f'removing_elocky_user: {_err[0]} HTTP Error: {e.__str__()}')
    except Exception as e:
        logger.debug(f'removing_elocky_user: {_err[0]} Error: {e.__str__()}')
    else:
        logger.debug(f'Removing user {_user.username} success')


