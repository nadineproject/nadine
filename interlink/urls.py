from django.urls import path

from interlink import views


app_name = 'interlink'
urlpatterns = [
    path('', views.home, name='home'),
    path('messages/<int:list_id>/', views.list_messages, name='messages'),
    path('subscribers/<int:list_id>/', views.list_subscribers, name='subscribers'),
    path('unsubscribe/<int:list_id>/<username>/', views.unsubscribe, name='unsubscribe'),
    path('subscribe/<int:list_id>/<username>/', views.subscribe, name='subscribe'),
    path('moderate/', views.moderator_list, name='moderate'),
    path('moderate/<int:id>/', views.moderator_inspect, name='inspect'),
    path('moderate/<int:id>/approve/', views.moderator_approve, name='approve'),
    path('moderate/<int:id>/reject/', views.moderator_reject, name='reject'),
]

# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

