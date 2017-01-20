from django.conf.urls import include, url
from django.shortcuts import redirect

from members.views import core, profile, organization, tags, connect, events, json

urlpatterns = [
    url(r'^$', core.home, name='member_home'),
    url(r'^faq/$', core.faq, name='member_faq'),
    url(r'^help/(?P<slug>[^/]+)/$', core.help_topic, name='member_help'),
    url(r'^view/$', core.view_members, name='member_members'),
    url(r'^register/$', core.register, name='member_register'),
    url(r'^manage/(?P<username>[^/]+)/$', core.manage_member, name='member_manage'),
    url(r'^not_active/$', core.not_active, name='member_not_active'),

    url(r'^profile/', include('members.urls.profile')),
    url(r'^organization/', include('members.urls.organization')),
    url(r'^tags/', include('members.urls.tags')),
    url(r'^connect/', include('members.urls.connect')),
    url(r'^events/', include('members.urls.events')),
    url(r'^json/', include('members.urls.json')),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
