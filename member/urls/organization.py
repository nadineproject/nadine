from django.conf.urls import url
from django.shortcuts import redirect

from member.views import organization

urlpatterns = [
    url(r'^$', organization.org_list, name='list'),
    url(r'^add/$', organization.org_add, name='add'),
    url(r'^(?P<org_id>\d+)/$', organization.org_view, name='view'),
    url(r'^(?P<org_id>\d+)/member/$', organization.org_member, name='member'),
    url(r'^(?P<org_id>\d+)/edit/$', organization.org_edit, name='edit'),
    url(r'^(?P<org_id>\d+)/edit_photo/$', organization.org_edit_photo, name='edit_photo'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
