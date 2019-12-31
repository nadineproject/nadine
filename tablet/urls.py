from django.shortcuts import redirect
from django.urls import include, path

from . import views

app_name = 'tablet'
urlpatterns = [
    path('', lambda r: redirect('tablet:motd'), name="home"),
    path('members/', views.members, name='members'),
    path('motd/', views.motd, name='motd'),
    path('here_today/', views.here_today, name='here_today'),
    path('visitors/', views.visitors, name='visitors'),
    path('search/', views.search, name='search'),
    path('welcome/<username>/', views.welcome, name='welcome'),
    path('profile/<username>/', views.user_profile, name='user_profile'),
    path('post_create/<username>/', views.post_create, name='post_create'),
    path('<username>/signin/', views.signin_user, name='signin_user'),
    path('<username>/guestof/<paid_by>/', views.signin_user_guest, name='signin_guest'),
    path('<username>/documents/', views.document_list, name='document_list'),
    path('<username>/document/<doc_type>/', views.document_view, name='document_view'),
    path('<username>/signature/<doc_type>/', views.signature_capture, name='sig_capture'),
    path('<username>/signature/<doc_type>/<signature_file>', views.signature_render, name='sig_render'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
