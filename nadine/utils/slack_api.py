# Forked from https://github.com/os/slacker
# Original Copyright 2015 Oktay Sancak

import json
import requests

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

API_BASE_URL = 'https://slack.com/api/{api}'
DEFAULT_TIMEOUT = 10

ERROR_MESSAGES = {
    'no_token': 'Please set your SLACK_API_TOKEN setting.',
}

__all__ = ['Error', 'Response', 'BaseAPI', 'API', 'Auth', 'Users', 'Groups',
           'Channels', 'Chat', 'IM', 'IncomingWebhook', 'Search', 'Files',
           'Stars', 'Emoji', 'Presence', 'RTM', 'Team', 'Reactions', 'Pins',
           'OAuth', 'SlackAPI']


def get_item_id_by_name(list_dict, key_name):
    for d in list_dict:
        if d['name'] == key_name:
            return d['id']

class Error(Exception):
    pass


class Response(object):
    def __init__(self, body):
        self.raw = body
        self.body = json.loads(body)
        self.ok = self.body['ok']
        self.error = self.body.get('error')

    def __repr__(self):
        if self.ok:
            return "Response OK: Size: %d, Keys: %s" % (len(self.raw), list(self.body.keys()))
        return "Response ERROR: %s" % self.error


class BaseAPI(object):
    def __init__(self, token=None, timeout=DEFAULT_TIMEOUT):
        self.token = token
        self.timeout = timeout

    def _request(self, method, api, **kwargs):
        if self.token:
            kwargs.setdefault('params', {})['token'] = self.token

        response = method(API_BASE_URL.format(api=api),
                          timeout=self.timeout,
                          **kwargs)

        response.raise_for_status()

        response = Response(response.text)
        if not response.ok:
            raise Error(response.error)

        return response

    def get(self, api, **kwargs):
        return self._request(requests.get, api, **kwargs)

    def post(self, api, **kwargs):
        return self._request(requests.post, api, **kwargs)


class API(BaseAPI):
    def test(self, error=None, **kwargs):
        if error:
            kwargs['error'] = error

        return self.get('api.test', params=kwargs)


class Auth(BaseAPI):
    def test(self):
        return self.get('auth.test')


class Users(BaseAPI):
    def info(self, user):
        return self.get('users.info', params={'user': user})

    def list(self):
        return self.get('users.list')

    def set_active(self):
        return self.post('users.setActive')

    def get_presence(self, user):
        return self.get('users.getPresence', params={'user': user})

    def set_presence(self, presence):
        assert presence in Presence.TYPES, 'Invalid presence type'
        return self.post('users.setPresence', data={'presence': presence})

    def get_user_id(self, user_name):
        members = self.list().body['members']
        return get_item_id_by_name(members, user_name)

    def invite(self, email, first_name=None, last_name=None):
        return self.post('users.admin.invite',
                         data={'email': email, 'set_active': 'true',
                               'first_name': first_name, 'last_name': last_name })


class Groups(BaseAPI):
    def create(self, name):
        return self.post('groups.create', data={'name': name})

    def create_child(self, channel):
        return self.post('groups.createChild', data={'channel': channel})

    def info(self, channel):
        return self.get('groups.info', params={'channel': channel})

    def list(self, exclude_archived=None):
        return self.get('groups.list',
                        params={'exclude_archived': exclude_archived})

    def history(self, channel, latest=None, oldest=None, count=None,
                inclusive=None):
        return self.get('groups.history',
                        params={
                            'channel': channel,
                            'latest': latest,
                            'oldest': oldest,
                            'count': count,
                            'inclusive': inclusive
                        })

    def invite(self, channel, user):
        return self.post('groups.invite',
                         data={'channel': channel, 'user': user})

    def kick(self, channel, user):
        return self.post('groups.kick',
                         data={'channel': channel, 'user': user})

    def leave(self, channel):
        return self.post('groups.leave', data={'channel': channel})

    def mark(self, channel, ts):
        return self.post('groups.mark', data={'channel': channel, 'ts': ts})

    def rename(self, channel, name):
        return self.post('groups.rename',
                         data={'channel': channel, 'name': name})

    def archive(self, channel):
        return self.post('groups.archive', data={'channel': channel})

    def unarchive(self, channel):
        return self.post('groups.unarchive', data={'channel': channel})

    def open(self, channel):
        return self.post('groups.open', data={'channel': channel})

    def close(self, channel):
        return self.post('groups.close', data={'channel': channel})

    def set_purpose(self, channel, purpose):
        return self.post('groups.setPurpose',
                         data={'channel': channel, 'purpose': purpose})

    def set_topic(self, channel, topic):
        return self.post('groups.setTopic',
                         data={'channel': channel, 'topic': topic})


class Channels(BaseAPI):
    def create(self, name):
        return self.post('channels.create', data={'name': name})

    def info(self, channel):
        return self.get('channels.info', params={'channel': channel})

    def list(self, exclude_archived=None):
        return self.get('channels.list',
                        params={'exclude_archived': exclude_archived})

    def history(self, channel, latest=None, oldest=None, count=None,
                inclusive=None):
        return self.get('channels.history',
                        params={
                            'channel': channel,
                            'latest': latest,
                            'oldest': oldest,
                            'count': count,
                            'inclusive': inclusive
                        })

    def mark(self, channel, ts):
        return self.post('channels.mark',
                         data={'channel': channel, 'ts': ts})

    def join(self, name):
        return self.post('channels.join', data={'name': name})

    def leave(self, channel):
        return self.post('channels.leave', data={'channel': channel})

    def invite(self, channel, user):
        return self.post('channels.invite',
                         data={'channel': channel, 'user': user})

    def kick(self, channel, user):
        return self.post('channels.kick',
                         data={'channel': channel, 'user': user})

    def rename(self, channel, name):
        return self.post('channels.rename',
                         data={'channel': channel, 'name': name})

    def archive(self, channel):
        return self.post('channels.archive', data={'channel': channel})

    def unarchive(self, channel):
        return self.post('channels.unarchive', data={'channel': channel})

    def set_purpose(self, channel, purpose):
        return self.post('channels.setPurpose',
                         data={'channel': channel, 'purpose': purpose})

    def set_topic(self, channel, topic):
        return self.post('channels.setTopic',
                         data={'channel': channel, 'topic': topic})

    def get_channel_id(self, channel_name):
        channels = self.list().body['channels']
        return get_item_id_by_name(channels, channel_name)


class Chat(BaseAPI):
    def post_message(self, channel, text, username=None, as_user=None,
                     parse=None, link_names=None, attachments=None,
                     unfurl_links=None, unfurl_media=None, icon_url=None,
                     icon_emoji=None):

        # Ensure attachments are json encoded
        if attachments:
            if isinstance(attachments, list):
                attachments = json.dumps(attachments)

        return self.post('chat.postMessage',
                         data={
                             'channel': channel,
                             'text': text,
                             'username': username,
                             'as_user': as_user,
                             'parse': parse,
                             'link_names': link_names,
                             'attachments': attachments,
                             'unfurl_links': unfurl_links,
                             'unfurl_media': unfurl_media,
                             'icon_url': icon_url,
                             'icon_emoji': icon_emoji
                         })

    def update(self, channel, ts, text):
        self.post('chat.update',
                  data={'channel': channel, 'ts': ts, 'text': text})

    def delete(self, channel, ts):
        self.post('chat.delete', data={'channel': channel, 'ts': ts})


class IM(BaseAPI):
    def list(self):
        return self.get('im.list')

    def history(self, channel, latest=None, oldest=None, count=None,
                inclusive=None):
        return self.get('im.history',
                        params={
                            'channel': channel,
                            'latest': latest,
                            'oldest': oldest,
                            'count': count,
                            'inclusive': inclusive
                        })

    def mark(self, channel, ts):
        return self.post('im.mark', data={'channel': channel, 'ts': ts})

    def open(self, user):
        return self.post('im.open', data={'user': user})

    def close(self, channel):
        return self.post('im.close', data={'channel': channel})


class Search(BaseAPI):
    def all(self, query, sort=None, sort_dir=None, highlight=None, count=None,
            page=None):
        return self.get('search.all',
                        params={
                            'query': query,
                            'sort': sort,
                            'sort_dir': sort_dir,
                            'highlight': highlight,
                            'count': count,
                            'page': page
                        })

    def files(self, query, sort=None, sort_dir=None, highlight=None,
              count=None, page=None):
        return self.get('search.files',
                        params={
                            'query': query,
                            'sort': sort,
                            'sort_dir': sort_dir,
                            'highlight': highlight,
                            'count': count,
                            'page': page
                        })

    def messages(self, query, sort=None, sort_dir=None, highlight=None,
                 count=None, page=None):
        return self.get('search.messages',
                        params={
                            'query': query,
                            'sort': sort,
                            'sort_dir': sort_dir,
                            'highlight': highlight,
                            'count': count,
                            'page': page
                        })


class Files(BaseAPI):
    def list(self, user=None, ts_from=None, ts_to=None, types=None,
             count=None, page=None):
        return self.get('files.list',
                        params={
                            'user': user,
                            'ts_from': ts_from,
                            'ts_to': ts_to,
                            'types': types,
                            'count': count,
                            'page': page
                        })

    def info(self, file_, count=None, page=None):
        return self.get('files.info',
                        params={'file': file_, 'count': count, 'page': page})

    def upload(self, file_, content=None, filetype=None, filename=None,
               title=None, initial_comment=None, channels=None):
        with open(file_, 'rb') as f:
            if isinstance(channels, (tuple, list)):
                channels = ','.join(channels)

            return self.post('files.upload',
                             data={
                                 'content': content,
                                 'filetype': filetype,
                                 'filename': filename,
                                 'title': title,
                                 'initial_comment': initial_comment,
                                 'channels': channels
                             },
                             files={'file': f})

    def delete(self, file_):
        return self.post('files.delete', data={'file': file_})


class Stars(BaseAPI):
    def list(self, user=None, count=None, page=None):
        return self.get('stars.list',
                        params={'user': user, 'count': count, 'page': page})


class Emoji(BaseAPI):
    def list(self):
        return self.get('emoji.list')


class Presence(BaseAPI):
    AWAY = 'away'
    ACTIVE = 'active'
    TYPES = (AWAY, ACTIVE)

    def set(self, presence):
        assert presence in Presence.TYPES, 'Invalid presence type'
        return self.post('presence.set', data={'presence': presence})


class RTM(BaseAPI):
    def start(self):
        return self.get('rtm.start')


class Team(BaseAPI):
    def info(self):
        return self.get('team.info')

    def access_logs(self, count=None, page=None):
        return self.get('team.accessLogs',
                        params={'count': count, 'page': page})


class Reactions(BaseAPI):
    def add(self, name, file_=None, file_comment=None, channel=None,
            timestamp=None):
        # One of file, file_comment, or the combination of channel and timestamp
        # must be specified
        assert (file_ or file_comment) or (channel and timestamp)

        return self.post('reactions.add',
                         data={
                             'name': name,
                             'file': file_,
                             'file_comment': file_comment,
                             'channel': channel,
                             'timestamp': timestamp,
                         })

    def get(self, file_=None, file_comment=None, channel=None, timestamp=None,
            full=None):
        return super(Reactions, self).get('reactions.get',
                                          params={
                                              'file': file_,
                                              'file_comment': file_comment,
                                              'channel': channel,
                                              'timestamp': timestamp,
                                              'full': full,
                                          })

    def list(self, user=None, full=None, count=None, page=None):
        return super(Reactions, self).get('reactions.list',
                                          params={
                                              'user': user,
                                              'full': full,
                                              'count': count,
                                              'page': page,
                                          })

    def remove(self, name, file_=None, file_comment=None, channel=None,
               timestamp=None):
        # One of file, file_comment, or the combination of channel and timestamp
        # must be specified
        assert (file_ or file_comment) or (channel and timestamp)

        return self.post('reactions.remove',
                         data={
                             'name': name,
                             'file': file_,
                             'file_comment': file_comment,
                             'channel': channel,
                             'timestamp': timestamp,
                         })


class Pins(BaseAPI):
    def add(self, channel, file_=None, file_comment=None, timestamp=None):
        # One of file, file_comment, or timestamp must also be specified
        assert file_ or file_comment or timestamp

        return self.post('pins.add',
                         data={
                             'channel': channel,
                             'file': file_,
                             'file_comment': file_comment,
                             'timestamp': timestamp,
                         })

    def remove(self, channel, file_=None, file_comment=None, timestamp=None):
        # One of file, file_comment, or timestamp must also be specified
        assert file_ or file_comment or timestamp

        return self.post('pins.remove',
                         data={
                             'channel': channel,
                             'file': file_,
                             'file_comment': file_comment,
                             'timestamp': timestamp,
                         })

    def list(self, channel):
        return self.get('pins.list', params={'channel': channel})


class OAuth(BaseAPI):
    def access(self, client_id, client_secret, code, redirect_uri=None):
        return self.post('oauth.access',
                         data={
                             'client_id': client_id,
                             'client_secret': client_secret,
                             'code': code,
                             'redirect_uri': redirect_uri
                         })


class IncomingWebhook(object):
    def __init__(self, url=None, timeout=DEFAULT_TIMEOUT):
        self.url = url
        self.timeout = timeout

    def post(self, data):
        """
        Posts message with payload formatted in accordance with
        this documentation https://api.slack.com/incoming-webhooks
        """
        if not self.url:
            raise Error('URL for incoming webhook is undefined')

        return requests.post(self.url, data=json.dumps(data),
                             timeout=self.timeout)

class SlackAPI:
    oauth = OAuth(timeout=DEFAULT_TIMEOUT)

    def __init__(self, incoming_webhook_url=None,
                 timeout=DEFAULT_TIMEOUT):

        token = getattr(settings, 'SLACK_API_TOKEN', None)
        if token is None:
            raise ImproperlyConfigured(ERROR_MESSAGES['no_token'])

        self.im = IM(token=token, timeout=timeout)
        self.api = API(token=token, timeout=timeout)
        self.rtm = RTM(token=token, timeout=timeout)
        self.auth = Auth(token=token, timeout=timeout)
        self.chat = Chat(token=token, timeout=timeout)
        self.team = Team(token=token, timeout=timeout)
        self.pins = Pins(token=token, timeout=timeout)
        self.users = Users(token=token, timeout=timeout)
        self.files = Files(token=token, timeout=timeout)
        self.stars = Stars(token=token, timeout=timeout)
        self.emoji = Emoji(token=token, timeout=timeout)
        self.search = Search(token=token, timeout=timeout)
        self.groups = Groups(token=token, timeout=timeout)
        self.channels = Channels(token=token, timeout=timeout)
        self.presence = Presence(token=token, timeout=timeout)
        self.reactions = Reactions(token=token, timeout=timeout)
        self.incomingwebhook = IncomingWebhook(url=incoming_webhook_url,
                                               timeout=timeout)
        self.user_cache = None

    def get_cached_members(self):
        if not self.user_cache:
            try:
                user_list = self.users.list()
                if user_list and user_list.ok:
                    self.user_cache = user_list.body['members']
            except:
                self.user_cache = None
        return self.user_cache

    def get_slack_member_id(self, user):
        for m in self.get_cached_members():
            if 'profile' in m:
                if 'email' in m['profile']:
                    if m['profile']['email'] == user.email:
                        return m['id']
        return None

    def invite_user(self, user):
        response = self.users.invite(user.email, first_name=user.first_name, last_name=user.last_name)
        return response.ok

    def invite_user_quiet(self, user):
        try:
            self.invite_user(user)
        except:
            pass

    def disable_user(self, user):
        # api call pulled from https://github.com/rjshenk/Slack-Admin-Tools
        slack_id = self.get_slack_member_id(user)
        if not slack_id:
            raise Exception("User not found")
        return self.api.post('users.admin.setInactive', data={'user':slack_id})

    def post_message(self, message, channel=None):
        if not channel:
            channel = "#General"
        self.chat.post_message(channel, message, as_user="Nadine")
