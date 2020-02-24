import time

from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

import views


admin.autodiscover()

app_name = 'nadine'
urlpatterns = [
    path('', views.index, name='site_index'),
    path('favicon.ico', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
    path('robots.txt', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    path('cache.manifest', lambda r: HttpResponse(get_manifest(), content_type="text/plain")),

    path('account/', include('django.contrib.auth.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.logout_then_login, name='logout'),

    path('staff/', include('staff.urls', namespace='staff')),
    path('member/', include('member.urls', namespace='member')),
    path('tablet/', include('tablet.urls', namespace='tablet')),
    path('doors/', include('doors.keymaster.urls', namespace='doors')),
    path('logs/', include('arpwatch.urls', namespace='arp')),
    path('comlink/', include('comlink.urls', namespace='comlink')),

    path('email/add/', views.email_add, name='email_add'),
    path('email/manage/<email_pk>/<action>/', views.email_manage, name='email_manage'),
    path('email/verify/<email_pk>/', views.email_verify, name='email_verify'),

    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def get_manifest():
    return "CACHE MANIFEST\n#Time: %s\nCACHE:\nFALLBACK:\nNETWORK:\n*" % time.time()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
