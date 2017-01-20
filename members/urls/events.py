from django.conf.urls import url
from django.shortcuts import redirect

from members.views import events

urlpatterns = [
    url(r'^events/$', events.events_google, name='member_events'),
    url(r'^booking/create/$', events.create_booking, name='member_create_booking'),
    url(r'^booking/confirm/(?P<room>[^/]+)/(?P<start>[^/]+)/(?P<end>[^/]+)/(?P<date>[^/]+)$', events.confirm_booking, name='member_confirm_booking'),
    url(r'^calendar/$', events.calendar, name='member_calendar'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
