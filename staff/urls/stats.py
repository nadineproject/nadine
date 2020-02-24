from django.urls import path

from staff.views import stats


app_name = 'staff'
urlpatterns = [
    path('daily/', stats.daily, name='daily'),
    path('history/', stats.history, name='history'),
    path('monthly/', stats.monthly, name='monthly'),
    path('gender/', stats.gender, name='gender'),
    path('neighborhood/', stats.neighborhood, name='neighborhood'),
    path('memberships/', stats.memberships, name='memberships'),
    path('longevity/', stats.longevity, name='longevity'),
    path('graph/', stats.graph, name='graph'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
