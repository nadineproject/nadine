from django.conf.urls import include, url

from staff.views import user

urlpatterns = [
     url(r'^members/$', user.members, name='members'),
     url(r'^members/(?P<group>[^/]+)/$', user.members, name='member_group'),
     url(r'^bcc/$', user.bcc_tool, name='bcc_tool'),
     url(r'^bcc/(?P<group>[^/]+)/$', user.bcc_tool, name='group_bcc'),
     url(r'^deposits/$', user.security_deposits, name='deposits'),
     url(r'^export/$', user.export_users, name='export_users'),
     url(r'^search/$', user.member_search, name='search'),
     url(r'^user_reports/$', user.view_user_reports, name='user_reports'),
     url(r'^slack_users/$', user.slack_users, name='slack_users'),
     url(r'^membership/(?P<username>[^/]+)/$', user.membership, name='membership'),
     url(r'^organizations/$', user.org_list, name='organizations'),
     url(r'^organization/(?P<org_id>\d+)$', user.org_view, name='organization'),

     url(r'^files/(?P<username>[^/]+)/$', user.files, name='files'),
     url(r'^detail/(?P<username>[^/]+)/$', user.detail, name='detail'),

     # TODO - remove
     url(r'^old/membership/(?P<membership_id>\d+)/$', user.old_membership, name='old_membership'),
     url(r'^old/add_membership/(?P<username>[^/]+)/$', user.old_add_membership, name='old_add_membership'),
     url(r'^old/memberships/(?P<username>[^/]+)/$', user.old_membership, name='old_memberships'),

     # TODO remove
     # url(r'^signins/(?P<username>[^/]+)/$', member.signins, name='user_signins'),
     # url(r'^signins/json/(?P<username>[^/]+)/$', member.signins_json, name='json_signins'),
     # url(r'^edit/(?P<username>[^/]+)/$', member.edit, name='user_edit'),

]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
