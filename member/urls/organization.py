from django.urls import path

from member.views import organization

app_name = 'member'
urlpatterns = [
    path('', organization.org_list, name='list'),
    path('add/', organization.org_add, name='add'),
    path('<int:org_id>/', organization.org_view, name='view'),
    path('<int:org_id>/member/', organization.org_member, name='member'),
    path('<int:org_id>/edit/', organization.org_edit, name='edit'),
    path('<int:org_id>/edit_photo/', organization.org_edit_photo, name='edit_photo'),
]

# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

