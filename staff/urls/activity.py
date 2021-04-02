from django.urls import path

from staff.views import activity


app_name = 'staff'
urlpatterns = [
    path('graph/', activity.graph, name='graph'),
    path('list/', activity.list, name='list'),
    path('today/', activity.for_today, name='today'),
    path('user/<username>/', activity.for_user, name='user'),
    path('date/<int:year>/<int:month>/<int:day>/', activity.for_date, name='date'),
]

# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

