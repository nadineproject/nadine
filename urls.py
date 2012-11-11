from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse

admin.autodiscover()

from nadine import API

urlpatterns = patterns('',
   (r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", mimetype="text/plain")),
   
   (r'^admin/', include(admin.site.urls)),
   (r'^staff/', include('staff.urls', app_name='staff')),
   (r'^member/', include('members.urls', app_name='members')),
   (r'^interlink/', include('interlink.urls', app_name='interlink')),
   (r'^logs/', include('arpwatch.urls', app_name='arpwatch')),
   (r'^tablet/', include('tablet.urls', app_name='tablet')),

   (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
   (r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
   (r'^accounts/profile/$', 'django.views.generic.simple.redirect_to', {'url': '/'}),

   (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),

   (r'^reset/$', 'front.views.password_reset', {'email_template_name':'front/email/password_reset_email.html'}),
   (r'^reset/done/$', 'django.contrib.auth.views.password_reset_done'),
   (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
   (r'^reset/complete/$', 'django.contrib.auth.views.password_reset_complete'),

   (r'^api/', include(API.urls)),

   (r'^', include('front.urls')),

)

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
