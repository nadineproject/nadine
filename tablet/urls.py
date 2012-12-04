from django.conf.urls.defaults import *

urlpatterns = patterns('tablet.views',
	(r'^$', 'signin'),
	(r'^signin/$', 'signin'),
	(r'^signin/(?P<username>[^/]+)/$', 'user_signin'),
	(r'^(?P<username>[^/]+)/signin/$', 'signin_user'),
	(r'^(?P<username>[^/]+)/guestof/(?P<guestof>[^/]+)$', 'signin_user_guest'),
	(r'^members/$', 'members'),
	(r'^member/(?P<username>[^/]+)/$', 'view_profile'),
	(r'^here_today/$', 'here_today'),
	(r'^search/$', 'search'),
	(r'^new/$', 'new_user'),
)

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
