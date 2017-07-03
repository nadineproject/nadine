from django.conf.urls import include, url

from staff.views import members

app_name = 'staff'
urlpatterns = [
     url(r'^members/$', members.members, name='members'),
     url(r'^members/(?P<group>[^/]+)/$', members.members, name='member_group'),
     url(r'^bcc/$', members.bcc_tool, name='bcc_tool'),
     url(r'^bcc/(?P<group>[^/]+)/$', members.bcc_tool, name='group_bcc'),
     url(r'^deposits/$', members.security_deposits, name='deposits'),
     url(r'^export/$', members.export_users, name='export_users'),
     url(r'^search/$', members.member_search, name='search'),
     url(r'^new_user/$', members.new_user, name='new_user'),
     url(r'^user_reports/$', members.view_user_reports, name='user_reports'),
     url(r'^slack_users/$', members.slack_users, name='slack_users'),
     url(r'^membership/(?P<username>[^/]+)/$', members.membership, name='membership'),
     url(r'^confirm/(?P<username>[^/]+)/(?P<package>[^/]+)/(?P<end_target>[^/]+)/(?P<start_target>[^/]+)/(?P<new_subs>[^/]+)/$', members.confirm_membership, name='confirm'),
     url(r'^edit_bill_day/(?P<username>[^/]+)/$', members.edit_bill_day, name='edit_bill_day'),
     url(r'^organizations/$', members.org_list, name='organizations'),
     url(r'^organization/(?P<org_id>\d+)$', members.org_view, name='organization'),

     url(r'^files/(?P<username>[^/]+)/$', members.files, name='files'),
     url(r'^detail/(?P<username>[^/]+)/$', members.detail, name='detail'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
