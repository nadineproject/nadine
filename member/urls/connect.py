from django.conf.urls import url
from django.shortcuts import redirect

from member.views import connect

app_name = 'member'
urlpatterns = [
    url(r'^notifications/$', connect.notifications, name='notifications'),
    url(r'^notifications/add/(?P<username>[^/]+)/$', connect.add_notification, name='add_notification'),
    url(r'^notifications/delete/(?P<username>[^/]+)/$', connect.delete_notification, name='del_notification'),
    url(r'^chat/$', connect.chat, name='chat'),
    url(r'^lists/$', connect.mail, name='email_lists'),
    url(r'^mail/(?P<id>\d+)/$', connect.mail_message, name='view_mail'),
    url(r'^slack/$', connect.slack_redirect, name='slack_redirect'),
    url(r'^slack/(?P<username>[^/]+)/$', connect.slack, name='slack'),
    url(r'^slack_bots/$', connect.slack_bots, name='slack_bot'),
    url(r'^(?P<username>[^/]+)/$', connect.connect, name='connect'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
