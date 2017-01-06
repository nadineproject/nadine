from django.shortcuts import redirect
from django.conf.urls import include, url

from staff.views import core

urlpatterns = [
    url(r'^$', lambda r: redirect('staff:tasks:todo'), name="index"),

    url(r'^tasks/', include('staff.urls.tasks', namespace="tasks")),
    url(r'^user/', include('staff.urls.user', namespace="user")),
    url(r'^activity/', include('staff.urls.activity', namespace="activity")),
    url(r'^billing/', include('staff.urls.billing', namespace="billing")),
    url(r'^settings/', include('staff.urls.settings', namespace="settings")),
    url(r'^stats/', include('staff.urls.stats', namespace="stats")),

    url(r'^view_ip/$', core.view_ip, name='view_ip'),
    url(r'^view_config/$', core.view_config, name='view_config'),

    url(r'^event/create$', core.create_event, name='create_event'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
