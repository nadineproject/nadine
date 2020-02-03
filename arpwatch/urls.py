from django.urls import path

from arpwatch import views


app_name = 'arpwatch'
urlpatterns = [
   path('', views.home, name='home'),
   path('import/', views.import_files, name='import'),
   path('devices/', views.device_list, name='devices'),
   path('device/(<int:device_id>)/', views.device, name='device'),
   path('device/', views.device_logs_today, name='devices_today'),
   path('device/<int:year>/<int:month>/<day>/', views.device_logs_by_day, name='device_logs'),
   path('user/', views.logins_today, name='user'),
   path('user/<int:year>/<int:month>/<int:day>/', views.logins_by_day, name='user_logs'),
]


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
