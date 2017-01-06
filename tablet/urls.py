from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^$', views.members),
    url(r'^members/$', views.members, name='tablet_members'),
    url(r'^here_today/$', views.here_today, name='tablet_here_today'),
    url(r'^visitors/$', views.visitors, name='tablet_visitors'),
    url(r'^search/$', views.search, name='tablet_search'),
    url(r'^welcome/(?P<username>[^/]+)$', views.welcome, name='tablet_welcome'),
    url(r'^signin/(?P<username>[^/]+)/$', views.user_signin, name='tablet_user_signin'),
    url(r'^profile/(?P<username>[^/]+)/$', views.user_profile, name='tablet_profile'),
    url(r'^post_create/(?P<username>[^/]+)/$', views.post_create, name='tablet_post_create'),
    url(r'^(?P<username>[^/]+)/signin/$', views.signin_user, name='tablet_signin_user'),
    url(r'^(?P<username>[^/]+)/guestof/(?P<paid_by>[^/]+)$', views.signin_user_guest, name='tablet_signin_guest'),
    url(r'^(?P<username>[^/]+)/documents/$', views.document_list, name='tablet_document_list'),
    url(r'^(?P<username>[^/]+)/document/(?P<doc_type>[^/]+)$', views.document_view, name='tablet_document_view'),
    url(r'^(?P<username>[^/]+)/signature/(?P<doc_type>[^/]+)/$', views.signature_capture, name='tablet_sig_capture'),
    url(r'^(?P<username>[^/]+)/signature/(?P<doc_type>[^/]+)/(?P<signature_file>[^/]+)$', views.signature_render, name='tablet_sig_render'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
