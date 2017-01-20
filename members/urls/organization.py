from django.conf.urls import url
from django.shortcuts import redirect

from members.views import organization

urlpatterns = [
    url(r'^organizations/$', organization.org_list, name='member_org_list'),
    url(r'^organizations/add/$', organization.org_add, name='member_org_add'),
    url(r'^organization/(?P<org_id>\d+)/$', organization.org_view, name='member_org_view'),
    url(r'^organization/(?P<org_id>\d+)/edit/$', organization.org_edit, name='member_org_edit'),
    url(r'^organization/(?P<org_id>\d+)/member/$', organization.org_member, name='member_org_member'),
    url(r'^edit_photo/organization/(?P<org_id>\d+)/$', organization.org_edit_photo, name='member_org_edit_photo'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
