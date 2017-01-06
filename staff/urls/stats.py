from django.conf.urls import include, url

from staff.views import stats

urlpatterns = [
    url(r'^daily/$', stats.daily, name='daily'),
    url(r'^history/$', stats.history, name='history'),
    url(r'^monthly/$', stats.monthly, name='monthly'),
    url(r'^gender/$', stats.gender, name='gender'),
    url(r'^neighborhood/$', stats.neighborhood, name='neighborhood'),
    url(r'^memberships/$', stats.memberships, name='memberships'),
    url(r'^longevity/$', stats.longevity, name='longevity'),
    url(r'^graph/$', stats.graph, name='graph'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
