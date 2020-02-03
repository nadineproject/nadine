from django.urls import include, path
from django.shortcuts import redirect

from member.views import core

app_name = 'member'
urlpatterns = [
    path('', core.home, name='home'),
    path('help/', core.help, name='help'),
    path('help/<slug:slug>/', core.help_topic, name='help_topic'),
    path('view/', core.view_members, name='members'),
    path('receipt/<int:bill_id>', core.bill_receipt, name='receipt'),
    path('register/', core.register, name='register'),
    path('manage/<username>/', core.manage_member, name='manage'),
    path('not_active/', core.not_active, name='not_active'),

    path('profile/', include('member.urls.profile', namespace='profile')),
    path('organization/', include('member.urls.organization', namespace="org")),
    path('tags/', include('member.urls.tags', namespace='tag')),
    path('connect/', include('member.urls.connect', namespace='connect')),
    path('events/', include('member.urls.events', namespace='event')),
    path('json/', include('member.urls.json', namespace='json')),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
