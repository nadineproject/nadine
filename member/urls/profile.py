from django.urls import path

from member.views import profile

app_name = 'member'
urlpatterns = [
    path('', profile.profile_redirect, name='redirect'),
    path('<username>/', profile.profile, name='view'),
    path('<username>/private/', profile.profile_private, name='private'),
    path('<username>/memberships/', profile.profile_membership, name='membership'),
    path('<username>/organizations/', profile.profile, name='orgs'),
    path('<username>/documents/', profile.profile_documents, name='documents'),
    path('<username>/events/', profile.profile_events, name='events'),
    path('<username>/activity/', profile.profile_activity, name='activity'),
    path('<username>/billing/', profile.profile_billing, name='billing'),
    path('<username>/devices/', profile.user_devices, name='devices'),
    path('<username>/edit/', profile.edit_profile, name='edit'),
    path('<username>/edit_photo/', profile.edit_photo, name='edit_photo'),
    path('<username>/disable_billing/', profile.disable_billing, name='disable_billing'),
    path('<username>/file/<disposition>/<file_name>', profile.file_view, name='file'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
