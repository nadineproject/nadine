import requests
from django.db import models
from django_cryptography.fields import encrypt
from datetime import datetime
from dateutil.parser import parse

from elocky.settings import *

CRYPTOGRAPHY_KEY = None

LIST_DAY = ["Not Found", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

class ElockyCred(models.Model):
    username = models.CharField(max_length=128, unique=True)
    elocky_id = models.CharField(max_length=128, unique=True)
    num_access = encrypt(models.CharField(max_length=128))
    code_access = encrypt(models.CharField(max_length=128))

    def __str__(self):
        return self.username

    @classmethod
    def sync_elocky_invite(cls, header=None):
        if header is None:
            url_login = 'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}

        url_list_access = 'https://www.elocky.com/webservice/access/list/invite.json'
        response = requests.get(url_list_access, headers=header)

        for access in response.json().get('access'):
            if access.get('type_access').get('id') == 4:
                cls.objects.update_or_create(username=access.get('name'), elocky_id=access.get('id'),
                                             defaults={
                                                 'num_access': access.get('num_access'),
                                                 'code_access': access.get('code_access')}
                                             )
        for access in ElockyCred.objects.all():
            if not any(str(d.get('id')) == access.elocky_id for d in response.json().get('access')):
                access.delete()

    def get_acces(self, header=None) -> dict:
        if header is None:
            url_login = 'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}
        url_list_access = 'https://www.elocky.com/webservice/access/list/invite.json'
        response = requests.get(url_list_access, headers=header)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)

        res_access = {'access_recu': [], 'access_exep': []}
        for access in response.json().get('access'):
            if str(access.get('id')) == self.elocky_id:
                for recu in access.get('access_recu'):
                    res_access['access_recu'].append({'start': parse(recu.get('start')).strftime("%H:%M:%S"),
                                                      'stop': parse(recu.get('stop')).strftime("%H:%M:%S"),
                                                      'state': recu.get('state'),
                                                      'day': LIST_DAY[int(recu.get('day').get('id', 0))],
                                                      'id': recu.get('id')
                                                      })
                for exep in access.get('access_exep'):
                    res_access['access_exep'].append({'start': parse(exep.get('start')).strftime("%d/%m/%Y %H:%M:%S"),
                                                      'stop': parse(exep.get('stop')).strftime("%d/%m/%Y %H:%M:%S"),
                                                      'state': exep.get('is_dispo'),
                                                      'id': exep.get('id')
                                                      })
                return res_access
        return res_access

    def remove_recu(self, access_id, header=None):
        if header is None:
            url_login = 'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}

        url_access = f'https://www.elocky.com/webservice/access/recu/delete/{access_id}.json'
        response = requests.delete(url_access, headers=header)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)

    def remove_exep(self, access_id, header=None):
        if header is None:
            url_login = 'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}

        url_access = f'https://www.elocky.com/webservice/access/exep/delete/{access_id}.json'
        response = requests.delete(url_access, headers=header)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)

    def recurent_access(self, start, stop, day, header=None):
        if header is None:
            url_login = f'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}

        url_access = f'https://www.elocky.com/webservice/access/recu/{self.elocky_id}.json'
        data_access = {'start': start, 'stop': stop, 'day': day}
        response = requests.post(url_access, headers=header, json=data_access)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)

    def exep_access(self, start, stop, header=None):
        if header is None:
            url_login = f'https://www.elocky.com/oauth/v2/token'
            data_login = {'client_id': ELOCKY_API_CLIENT_ID, 'client_secret': ELOCKY_API_CLIENT_SECRET,
                          'grant_type': 'password',
                          'username': ELOCKY_USERNAME, 'password': ELOCKY_PASSWORD}
            response = requests.post(url_login, json=data_login)
            if response.ok is False:
                raise requests.exceptions.HTTPError(response)
            access_token = response.json().get('access_token')
            header = {'Authorization': f'Bearer {access_token}'}

        url_access = f'https://www.elocky.com/webservice/access/exep/{self.elocky_id}.json'
        data_access = {'start': start, 'stop': stop, 'isDispo': True}
        response = requests.post(url_access, headers=header, json=data_access)
        if response.ok is False:
            raise requests.exceptions.HTTPError(response)
