from django.conf.urls import include, url
from django.shortcuts import redirect

from member.views import core

urlpatterns = [
    url(r'^$', core.home, name='home'),
    url(r'^faq/$', core.faq, name='faq'),
    url(r'^help/(?P<slug>[^/]+)/$', core.help_topic, name='help'),
    url(r'^view/$', core.view_members, name='members'),
    url(r'^register/$', core.register, name='register'),
    url(r'^manage/(?P<username>[^/]+)/$', core.manage_member, name='manage'),
    url(r'^not_active/$', core.not_active, name='not_active'),

    url(r'^profile/', include('member.urls.profile', namespace='profile')),
    url(r'^organization/', include('member.urls.organization', namespace="org")),
    url(r'^tags/', include('member.urls.tags', namespace='tag')),
    url(r'^connect/', include('member.urls.connect', namespace='connect')),
    url(r'^events/', include('member.urls.events', namespace='event')),
    url(r'^json/', include('member.urls.json', namespace='json')),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
