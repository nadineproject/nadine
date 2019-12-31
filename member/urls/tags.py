from django.urls import path

from member.views import tags

app_name = 'member'
urlpatterns = [
    path('list/<type>/', tags.tag_list, name='list'),
    path('cloud/<type>/', tags.tag_cloud, name='cloud'),
    path('add/user/<username>/', tags.add_tag, name='add'),
    path('remove/user/<username>/<tag>/', tags.remove_tag, name='remove'),
    path('add/org/<int:org_id>/', tags.add_org_tag, name='add_org'),
    path('remove/org/<int:org_id>/<tag>/', tags.remove_org_tag, name='remove_org'),
    path('<type>/<tag>/', tags.tag_view, name='view'),

]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
