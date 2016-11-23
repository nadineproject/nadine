from django.conf.urls import url
from django.shortcuts import redirect

from members.views import core, profile, organization, tags, connect, events, json

urlpatterns = [
    # Core
    url(r'^$', core.home, name='member_home'),
    url(r'^faq/$', core.faq, name='member_faq'),
    url(r'^help/(?P<slug>[^/]+)/$', core.help_topic, name='member_help'),
    url(r'^view/$', core.view_members, name='member_members'),
    url(r'^register/$', core.register, name='member_register'),
    url(r'^manage/(?P<username>[^/]+)/$', core.manage_member, name='member_manage'),
    url(r'^not_active/$', core.not_active, name='member_not_active'),

    # Profile
    url(r'^profile/$', profile.profile_redirect, name='member_profile_redirect'),
    url(r'^profile/(?P<username>[^/]+)/$', profile.profile, name='member_profile'),
    url(r'^profile/(?P<username>[^/]+)/private/$', profile.profile_private, name='member_profile_private'),
    url(r'^profile/(?P<username>[^/]+)/memberships/$', profile.profile_membership, name='member_profile_membership'),
    url(r'^profile/(?P<username>[^/]+)/organizations/$', profile.profile_orgs, name='member_profile_orgs'),
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

    # Organization
    url(r'^organizations/$', organization.org_list, name='member_org_list'),
    url(r'^organization/(?P<org_id>\d+)/$', organization.org_view, name='member_org_view'),
    url(r'^organization/(?P<org_id>\d+)/edit/$', organization.org_edit, name='member_org_edit'),
    url(r'^organization/(?P<org_id>\d+)/member/$', organization.org_member, name='member_org_member'),
    url(r'^edit_photo/organization/(?P<org_id>\d+)/$', organization.org_edit_photo, name='member_org_edit_photo'),
    url(r'^organization/(?P<org_id>\d+)/tags/$', organization.add_tag, name='member_org_add_tag'),
    url(r'^del_tag/(?P<org_id>\d+)/(?P<tag>[^/]+)/$', organization.remove_tag, name='member_org_remove_tag'),

    # Tags
    url(r'^tag_list/$', tags.tags, name='member_tags'),
    url(r'^tag_cloud/$', tags.tag_cloud, name='member_tag_cloud'),
    url(r'^tag/(?P<tag>[^/]+)/$', tags.tag, name='member_tag'),
    url(r'^tag/remove/(?P<username>[^/]+)/(?P<tag>[^/]+)/$', tags.remove_tag, name='member_remove_tag'),
    url(r'^tag/add/(?P<username>[^/]+)/$', tags.add_tag, name='member_add_tag'),
    url(r'^org_tag_cloud/$', tags.org_tag_cloud, name='member_org_tag_cloud'),

    # Connect
    url(r'^connect/(?P<username>[^/]+)/$', connect.connect, name='member_connect'),
    url(r'^notifications/$', connect.notifications, name='member_notifications'),
    url(r'^notifications/add/(?P<username>[^/]+)/$', connect.add_notification, name='member_add_notification'),
    url(r'^notifications/delete/(?P<username>[^/]+)/$', connect.delete_notification, name='member_del_notification'),
    url(r'^chat/$', connect.chat, name='member_chat'),
    url(r'^lists/$', connect.mail, name='member_email_lists'),
    url(r'^mail/(?P<id>\d+)/$', connect.mail_message, name='member_view_mail'),
    url(r'^slack/(?P<username>[^/]+)/$', connect.slack, name='member_slack'),
    url(r'^slack_bots/$', connect.slack_bots, name='member_slack_bot'),

    # Events
    url(r'^events/$', events.events_google, name='member_events'),
    url(r'^booking/create/$', events.create_booking, name='member_create_booking'),
    url(r'^booking/confirm/(?P<room>[^/]+)/(?P<start>[^/]+)/(?P<end>[^/]+)/(?P<date>[^/]+)$', events.confirm_booking, name='member_confirm_booking'),
    url(r'^calendar/$', events.calendar, name='member_calendar'),

    # JSON
    url(r'^json/user_search/$', json.user_search, name='json_user_search'),
    url(r'^json/user_tags/$', json.user_tags, name='json_user_tags'),
    url(r'^json/org_tags/$', json.org_tags, name='json_org_tags'),
    url(r'^json/org_search/$', json.org_search, name='json_org_search'),
]

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
