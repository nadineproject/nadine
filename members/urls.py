from django.conf.urls import patterns, include, url
from django.shortcuts import redirect
from members import views

# urlpatterns = patterns('gather.views',
#	url(r'^events/$', 'upcoming_events'),
#)

urlpatterns = patterns('members.views',
                       (r'^$', 'home'),
                       (r'^view/$', 'view_members'),
                       (r'^events/$', 'events_google'),
                       (r'^chat/$', 'chat'),
                       (r'^tag_list/$', 'tags'),
                       (r'^tag_cloud/$', 'tag_cloud'),
                       (r'^not_active/$', 'not_active'),
                       (r'^tag/(?P<tag>[^/]+)/$', 'tag'),
                       (r'^profile/$', 'profile_redirect'),
                       (r'^profile/(?P<username>[^/]+)/$', 'user'),
                       (r'^manage/(?P<username>[^/]+)/$', 'manage_member'),
                       (r'^user_tags/(?P<username>[^/]+)/$', 'user_tags'),
                       (r'^del_tag/(?P<username>[^/]+)/(?P<tag>[^/]+)/$', 'delete_tag'),
                       (r'^slack/(?P<username>[^/]+)/$', 'slack'),
                       (r'^devices/(?P<username>[^/]+)/$', 'user_devices'),
                       (r'^edit/(?P<username>[^/]+)/$', 'edit_profile'),
                       (r'^receipt/(?P<username>[^/]+)/(?P<id>\d+)/$', 'receipt'),
                       (r'^connect/(?P<username>[^/]+)/$', 'connect'),
                       (r'^help/(?P<slug>[^/]+)/$', 'help_topic'),
                       (r'^lists/$', 'mail'),
                       (r'^mail/(?P<id>\d+)/$', 'mail_message'),
                       (r'^notifications/$', 'notifications'),
                       (r'^notifications/add/(?P<username>[^/]+)/$', 'add_notification'),
                       (r'^notifications/delete/(?P<username>[^/]+)/$', 'delete_notification'),
                       (r'^disable_billing/(?P<username>[^/]+)$', 'disable_billing'),
                       (r'^file/(?P<disposition>[^/]+)/(?P<username>[^/]+)/(?P<file_name>[^/]+)$', 'file_view'),
                       )

# Copyright 2014 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
