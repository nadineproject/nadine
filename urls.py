import time
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from django.contrib.auth.views import login, logout_then_login, password_reset_done, password_reset_confirm, password_reset_complete

import views

admin.autodiscover()

favicon_view = RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    url(r'^cache\.manifest$', lambda r: HttpResponse(get_manifest(), content_type="text/plain")),
    url(r'^favicon\.ico$', favicon_view),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^staff/', include('staff.urls')),
    url(r'^member/', include('members.urls')),
    url(r'^interlink/', include('interlink.urls')),
    url(r'^doors/', include('doors.keymaster.urls')),
    url(r'^logs/', include('arpwatch.urls')),
    url(r'^tablet/', include('tablet.urls')),

    url(r'^login/$', login, {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', logout_then_login, name="logout"),
    url(r'^accounts/profile/$', lambda r: redirect('/')),

    url(r'^email/add/$', views.email_add, name='email_add'),
    url(r'^email/manage/(?P<email_pk>\d+)/(?P<action>.+)/$', views.email_manage, name='email_manage'),
    url(r'^email/verify/(?P<email_pk>\d+)/$', views.email_verify, name='email_verify'),

    url(r'^reset/$', views.password_reset, {'template_name': 'password_reset_form.html', 'email_template_name': 'email/password_reset_email.txt'}, 'password_reset'),
    url(r'^reset/done/$', password_reset_done, {'template_name': 'password_reset_done.html'}, 'password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm, {'template_name': 'password_reset_confirm.html'}, 'password_reset_confirm'),
    url(r'^reset/complete/$', password_reset_complete, {'template_name': 'password_reset_complete.html'}, 'password_reset_complete'),

    # Comlink URLS
    url('^comlink/', include('comlink.urls')),

    url(r'^$', views.index, name='site_index'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def get_manifest():
    return "CACHE MANIFEST\n#Time: %s\nCACHE:\nFALLBACK:\nNETWORK:\n*" % time.time()


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
