from django.conf.urls import url
from django.shortcuts import redirect

from member.views import profile

app_name = 'member'
urlpatterns = [
    url(r'^$', profile.profile_redirect, name='redirect'),
    url(r'^(?P<username>[^/]+)/$', profile.profile, name='view'),
    url(r'^(?P<username>[^/]+)/private/$', profile.profile_private, name='private'),
    url(r'^(?P<username>[^/]+)/memberships/$', profile.profile_membership, name='membership'),
    url(r'^(?P<username>[^/]+)/organizations/$', profile.profile, name='orgs'),
    url(r'^(?P<username>[^/]+)/documents/$', profile.profile_documents, name='documents'),
    url(r'^(?P<username>[^/]+)/events/$', profile.profile_events, name='events'),
    url(r'^(?P<username>[^/]+)/activity/$', profile.profile_activity, name='activity'),
    url(r'^(?P<username>[^/]+)/billing/$', profile.profile_billing, name='billing'),
    url(r'^(?P<username>[^/]+)/devices/$', profile.user_devices, name='devices'),
    url(r'^(?P<username>[^/]+)/edit/$', profile.edit_profile, name='edit'),
    url(r'^(?P<username>[^/]+)/edit_photo/$', profile.edit_photo, name='edit_photo'),
    url(r'^(?P<username>[^/]+)/disable_billing/$', profile.disable_billing, name='disable_billing'),
    url(r'^(?P<username>[^/]+)/file/(?P<disposition>[^/]+)/(?P<file_name>[^/]+)$', profile.file_view, name='file'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
