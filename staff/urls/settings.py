from django.conf.urls import include, url

from staff.views import settings

urlpatterns = [
     url(r'^$', settings.index, name='index'),
     url(r'^helptexts/$', settings.helptexts, name='helptexts'),
     url(r'^motd/$', settings.motd, name='motd'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
