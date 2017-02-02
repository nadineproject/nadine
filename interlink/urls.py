from django.conf.urls import url

from interlink import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^messages/(?P<list_id>[^/]+)/$', views.list_messages, name='messages'),
    url(r'^subscribers/(?P<list_id>[^/]+)/$', views.list_subscribers, name='subscribers'),
    url(r'^unsubscribe/(?P<list_id>[^/]+)/(?P<username>[^/]+)$', views.unsubscribe, name='unsubscribe'),
    url(r'^subscribe/(?P<list_id>[^/]+)/(?P<username>[^/]+)$', views.subscribe, name='subscribe'),
    url(r'^moderate/$', views.moderator_list, name='moderate'),
    url(r'^moderate/(?P<id>[\d]+)/$', views.moderator_inspect, name='inspect'),
    url(r'^moderate/(?P<id>[\d]+)/approve/$', views.moderator_approve, name='approve'),
    url(r'^moderate/(?P<id>[\d]+)/reject/$', views.moderator_reject, name='reject'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
