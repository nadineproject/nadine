import time
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect

admin.autodiscover()

#from tastypie.api import Api
#from arpwatch.api import ActivityResource
#API = Api(api_name='v1')
#API.register(ActivityResource())

urlpatterns = patterns('',
                       url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
                       url(r'^cache\.manifest$', lambda r: HttpResponse(get_manifest(), content_type="text/plain")),

                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^staff/', include('staff.urls')),
                       url(r'^member/', include('members.urls')),
                       url(r'^interlink/', include('interlink.urls')),
                       url(r'^doors/', include('doors.keymaster.urls')),
                       url(r'^logs/', include('arpwatch.urls')),
                       url(r'^tablet/', include('tablet.urls')),

                       url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
                       url(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
                       url(r'^accounts/profile/$', lambda r: redirect('/')),

                       url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

                       url(r'^reset/$', 'views.password_reset', {'template_name': 'password_reset_form.html', 'email_template_name': 'email/password_reset_email.txt'}, 'password_reset'),
                       url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_done', {'template_name': 'password_reset_done.html'}, 'password_reset_done'),
                       url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {'template_name': 'password_reset_confirm.html'}, 'password_reset_confirm'),
                       url(r'^reset/complete/$', 'django.contrib.auth.views.password_reset_complete', {'template_name': 'password_reset_complete.html'}, 'password_reset_complete'),

                       # API URLs
                       #url(r'^api/', include(API.urls)),

                       # Inbound Mailgun Emails
                       url(r'^mailgun/staff$', 'nadine.mailgun.staff'),
                       url(r'^mailgun/team$', 'nadine.mailgun.team'),
                       url(r'^mailgun/test80085$', 'nadine.mailgun.test80085'),

                       # Discourse discussion group
                       url(r'^discourse/sso$', 'nadine.discourse.sso'),

                       url(r'^$', 'views.index'),
                       )

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )


def get_manifest():
    return "CACHE MANIFEST\n#Time: %s\nCACHE:\nFALLBACK:\nNETWORK:\n*" % time.time()


# Copyright 2014 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
