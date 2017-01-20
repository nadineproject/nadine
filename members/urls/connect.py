from django.conf.urls import url
from django.shortcuts import redirect

from members.views import connect

urlpatterns = [
    url(r'^connect/(?P<username>[^/]+)/$', connect.connect, name='member_connect'),
    url(r'^notifications/$', connect.notifications, name='member_notifications'),
    url(r'^notifications/add/(?P<username>[^/]+)/$', connect.add_notification, name='member_add_notification'),
    url(r'^notifications/delete/(?P<username>[^/]+)/$', connect.delete_notification, name='member_del_notification'),
    url(r'^chat/$', connect.chat, name='member_chat'),
    url(r'^lists/$', connect.mail, name='member_email_lists'),
    url(r'^mail/(?P<id>\d+)/$', connect.mail_message, name='member_view_mail'),
    url(r'^slack/(?P<username>[^/]+)/$', connect.slack, name='member_slack'),
    url(r'^slack_bots/$', connect.slack_bots, name='member_slack_bot'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
