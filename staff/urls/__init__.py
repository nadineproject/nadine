from django.urls import include, path
from django.shortcuts import redirect

from staff.views import core

app_name = 'staff'
urlpatterns = [
    path('', lambda r: redirect('staff:tasks:todo'), name="home"),

    # A url file for every tab
    path('tasks/', include('staff.urls.tasks', namespace="tasks")),
    path('members/', include('staff.urls.members', namespace="members")),
    path('activity/', include('staff.urls.activity', namespace="activity")),
    path('billing/', include('staff.urls.billing', namespace="billing")),
    path('stats/', include('staff.urls.stats', namespace="stats")),
    path('mailing_lists/', include('staff.urls.mailing_lists', namespace="mailing_lists")),
    path('settings/', include('staff.urls.settings', namespace="settings")),
    # Logs == Arpwatch
    # Doors = Doors

    # Other URLS
    path('event/create/', core.create_event, name='create_event'),
]

# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

