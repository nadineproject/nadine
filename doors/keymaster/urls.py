from django.urls import path

from doors.keymaster import views


app_name = 'doors'
urlpatterns = [
    path('', views.home, name='home'),
    path('logs/', views.logs, name='logs'),
    path('keys/<username>/', views.user_keys, name='keys'),
    path('users/', views.user_list, name='users'),
    path('add_key/', views.add_key, name='add_key'),
    path('test_door/', views.test_door, name='test'),
    path('keymaster/', views.keymaster, name='keymaster'),
]


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

