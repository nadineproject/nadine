from django.conf.urls import url
from django.shortcuts import redirect

from members.views import profile

urlpatterns = [
    url(r'^profile/$', profile.profile_redirect, name='member_profile_redirect'),
    url(r'^profile/(?P<username>[^/]+)/$', profile.profile, name='member_profile'),
    url(r'^profile/(?P<username>[^/]+)/private/$', profile.profile_private, name='member_profile_private'),
    url(r'^profile/(?P<username>[^/]+)/memberships/$', profile.profile_membership, name='member_profile_membership'),
    url(r'^profile/(?P<username>[^/]+)/organizations/$', profile.profile, name='member_profile_orgs'),
    url(r'^profile/(?P<username>[^/]+)/documents/$', profile.profile_documents, name='member_profile_documents'),
    url(r'^profile/(?P<username>[^/]+)/activity/$', profile.profile_activity, name='member_profile_activity'),
    url(r'^profile/(?P<username>[^/]+)/billing/$', profile.profile_billing, name='member_profile_billing'),
    url(r'^profile/(?P<username>[^/]+)/devices/$', profile.user_devices, name='member_profile_devices'),
    url(r'^edit/(?P<username>[^/]+)/$', profile.edit_profile, name='member_edit_profile'),
    url(r'^receipt/(?P<username>[^/]+)/(?P<id>\d+)/$', profile.receipt, name='member_receipt'),
    url(r'^disable_billing/(?P<username>[^/]+)$', profile.disable_billing, name='member_disable_billing'),
    url(r'^file/(?P<disposition>[^/]+)/(?P<username>[^/]+)/(?P<file_name>[^/]+)$', profile.file_view, name='member_files'),
    url(r'^edit_pic/(?P<username>[^/]+)/$', profile.edit_pic, name='member_edit_pic'),
    url(r'^edit_photo/(?P<username>[^/]+)/$', profile.edit_photo, name='member_edit_photo'),
    url(r'^activity/(?P<username>[^/]+)/json/$', profile.user_activity_json, name='member_activity_json'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
