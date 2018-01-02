from django.conf.urls import url

from arpwatch import views

app_name = 'arpwatch'
urlpatterns = [
   url(r'^$', views.home, name='home'),
   url(r'^import/$', views.import_files, name='import'),
   url(r'^devices/$', views.device_list, name='devices'),
   url(r'^device/(?P<device_id>[\d]+)/$', views.device, name='device'),
   url(r'^device/$', views.device_logs_today, name='devices_today'),
   url(r'^device/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', views.device_logs_by_day, name='device_logs'),
   url(r'^user/$', views.logins_today, name='user'),
   url(r'^user/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', views.logins_by_day, name='user_logs'),
]


# Copyright 2018 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
