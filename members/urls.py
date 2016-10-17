from django.conf.urls import url
from django.shortcuts import redirect

from members import views

urlpatterns = [
    url(r'^$', views.home, name='member_home'),
    url(r'^view/$', views.view_members, name='member_members'),
    url(r'^events/$', views.events_google, name='member_events'),
    url(r'^faq/$', views.faq, name='member_faq'),
    url(r'^chat/$', views.chat, name='member_chat'),
    url(r'^register/$', views.register, name='member_register'),
    url(r'^tag_list/$', views.tags, name='member_tags'),
    url(r'^tag_cloud/$', views.tag_cloud, name='member_tag_cloud'),
    url(r'^tag/(?P<tag>[^/]+)/$', views.tag, name='member_tag'),
    url(r'^not_active/$', views.not_active, name='member_not_active'),
    url(r'^profile/$', views.profile_redirect, name='member_profile_redirect'),
    url(r'^profile/(?P<username>[^/]+)/$', views.user, name='member_profile'),
    url(r'^profile/(?P<username>[^/]+)/memberships/$', views.profile_membership, name='member_profile_membership'),
    url(r'^profile/(?P<username>[^/]+)/activity/$', views.profile_activity, name='member_profile_activity'),
    url(r'^profile/(?P<username>[^/]+)/billing/$', views.profile_billing, name='member_profile_billing'),
    url(r'^activity/(?P<username>[^/]+)/json/$', views.user_activity_json, name='member_activity_json'),
    url(r'^manage/(?P<username>[^/]+)/$', views.manage_member, name='member_manage'),
    url(r'^user_tags/(?P<username>[^/]+)/$', views.user_tags, name='member_user_tags'),
    url(r'^del_tag/(?P<username>[^/]+)/(?P<tag>[^/]+)/$', views.delete_tag, name='member_remove_tag'),
    url(r'^slack/(?P<username>[^/]+)/$', views.slack, name='member_slack'),
    url(r'^slack_bots/$', views.slack_bots, name='member_slack_bot'),
    url(r'^devices/(?P<username>[^/]+)/$', views.user_devices, name='member_user_devices'),
    url(r'^edit/(?P<username>[^/]+)/$', views.edit_profile, name='member_edit_profile'),
    url(r'^receipt/(?P<username>[^/]+)/(?P<id>\d+)/$', views.receipt, name='member_receipt'),
    url(r'^connect/(?P<username>[^/]+)/$', views.connect, name='member_connect'),
    url(r'^help/(?P<slug>[^/]+)/$', views.help_topic, name='member_help'),
    url(r'^lists/$', views.mail, name='member_email_lists'),
    url(r'^mail/(?P<id>\d+)/$', views.mail_message, name='member_view_mail'),
    url(r'^notifications/$', views.notifications, name='member_notifications'),
    url(r'^notifications/add/(?P<username>[^/]+)/$', views.add_notification, name='member_add_notification'),
    url(r'^notifications/delete/(?P<username>[^/]+)/$', views.delete_notification, name='member_del_notification'),
    url(r'^disable_billing/(?P<username>[^/]+)$', views.disable_billing, name='member_disable_billing'),
    url(r'^file/(?P<disposition>[^/]+)/(?P<username>[^/]+)/(?P<file_name>[^/]+)$', views.file_view, name='member_files'),
    url(r'^booking/create/$', views.create_booking, name='member_create_booking'),
    url(r'^booking/confirm/(?P<room>[^/]+)/(?P<start>[^/]+)/(?P<end>[^/]+)/(?P<date>[^/]+)$', views.confirm_booking, name='member_confirm_booking'),
    url(r'^calendar/$', views.calendar, name='member_calendar'),
]

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
