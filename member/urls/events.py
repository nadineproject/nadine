from django.urls import path

from member.views import events

app_name = 'member'
urlpatterns = [
    path('events/', events.events_google, name='events'),
    path('booking/create/<username>/', events.create_booking, name='create_booking'),
    path('booking/confirm/<room>/<start>/<end>/<date>/<rate>/', events.confirm_booking, name='confirm_booking'),
    path('calendar/', events.calendar, name='calendar'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
