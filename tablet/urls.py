from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

urlpatterns = patterns('tablet.views',
	url(r'^$', 'members'),
	url(r'^members/$', 'members'),
	url(r'^here_today/$', 'here_today'),
	url(r'^visitors/$', 'visitors'),
	url(r'^search/$', 'search'),
	url(r'^welcome/(?P<username>[^/]+)$', 'welcome'),
	url(r'^signin/(?P<username>[^/]+)/$', 'user_signin'),
	url(r'^profile/(?P<username>[^/]+)/$', 'user_profile'),
	url(r'^post_create/(?P<username>[^/]+)/$', 'post_create'),
	url(r'^(?P<username>[^/]+)/signin/$', 'signin_user'),
	url(r'^(?P<username>[^/]+)/guestof/(?P<guestof>[^/]+)$', 'signin_user_guest'),
	url(r'^(?P<username>[^/]+)/signature/$', 'signature_capture'),
	url(r'^(?P<username>[^/]+)/signature/(?P<signature_key>[^/]+)$', 'signature_accept'),
)

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
