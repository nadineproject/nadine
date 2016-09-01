from django.conf.urls import url
from django.shortcuts import redirect
from members import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^view/$', views.view_members),
    url(r'^events/$', views.events_google),
    url(r'^faq/$', views.faq),
    url(r'^chat/$', views.chat),
    url(r'^register/$', views.register),
    url(r'^tag_list/$', views.tags),
    url(r'^tag_cloud/$', views.tag_cloud),
    url(r'^not_active/$', views.not_active),
    url(r'^tag/(?P<tag>[^/]+)/$', views.tag),
    url(r'^profile/$', views.profile_redirect),
    url(r'^profile/(?P<username>[^/]+)/$', views.user),
    url(r'^manage/(?P<username>[^/]+)/$', views.manage_member),
    url(r'^user_tags/(?P<username>[^/]+)/$', views.user_tags),
    url(r'^del_tag/(?P<username>[^/]+)/(?P<tag>[^/]+)/$', views.delete_tag),
    url(r'^slack/(?P<username>[^/]+)/$', views.slack),
    url(r'^slack_bots/$', views.slack_bots),
    url(r'^devices/(?P<username>[^/]+)/$', views.user_devices),
    url(r'^edit/(?P<username>[^/]+)/$', views.edit_profile),
    url(r'^receipt/(?P<username>[^/]+)/(?P<id>\d+)/$', views.receipt),
    url(r'^connect/(?P<username>[^/]+)/$', views.connect),
    url(r'^help/(?P<slug>[^/]+)/$', views.help_topic),
    url(r'^lists/$', views.mail),
    url(r'^mail/(?P<id>\d+)/$', views.mail_message),
    url(r'^notifications/$', views.notifications),
    url(r'^notifications/add/(?P<username>[^/]+)/$', views.add_notification),
    url(r'^notifications/delete/(?P<username>[^/]+)/$', views.delete_notification),
    url(r'^disable_billing/(?P<username>[^/]+)$', views.disable_billing),
    url(r'^file/(?P<disposition>[^/]+)/(?P<username>[^/]+)/(?P<file_name>[^/]+)$', views.file_view),
]

# Copyright 2014 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
