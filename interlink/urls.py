from django.conf.urls import patterns, include, url
from django.conf import settings

from models import *

urlpatterns = patterns('',
   (r'^messages/(?P<list_id>[^/]+)/$', 'interlink.views.list_messages'),
   (r'^subscribers/(?P<list_id>[^/]+)/$', 'interlink.views.list_subscribers'),
   (r'^unsubscribe/(?P<list_id>[^/]+)/(?P<username>[^/]+)$', 'interlink.views.unsubscribe'),
   (r'^subscribe/(?P<list_id>[^/]+)/(?P<username>[^/]+)$', 'interlink.views.subscribe'),
   (r'^moderate/$', 'interlink.views.moderator_list'),
   (r'^moderate/(?P<id>[\d]+)/$', 'interlink.views.moderator_inspect'),
   (r'^moderate/(?P<id>[\d]+)/approve/$', 'interlink.views.moderator_approve'),
   (r'^moderate/(?P<id>[\d]+)/reject/$', 'interlink.views.moderator_reject'),
	(r'^$', 'interlink.views.index'),
)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
