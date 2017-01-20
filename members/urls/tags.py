from django.conf.urls import url
from django.shortcuts import redirect

from members.views import tags

urlpatterns = [
    url(r'^(?P<type>[^/]+)/(?P<tag>[^/]+)/$', tags.tag_view, name='view'),
    url(r'^list/(?P<type>[^/]+)/$', tags.tag_list, name='list'),
    url(r'^cloud/(?P<type>[^/]+)/$', tags.tag_cloud, name='cloud'),
    url(r'^add/user/(?P<username>[^/]+)/$', tags.add_tag, name='add'),
    url(r'^remove/user/(?P<username>[^/]+)/(?P<tag>[^/]+)/$', tags.remove_tag, name='remove'),
    url(r'^add/org/(?P<org_id>\d+)/$', tags.add_org_tag, name='add_org'),
    url(r'^remove/org/(?P<org_id>\d+)/(?P<tag>[^/]+)/$', tags.remove_org_tag, name='remove_org'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
