from django.conf.urls import include, url

from staff.views import member

urlpatterns = [
     url(r'^detail/(?P<username>[^/]+)/$', member.detail, name='detail'),
     url(r'^transactions/(?P<username>[^/]+)/$', member.transactions, name='transactions'),
     url(r'^bills/(?P<username>[^/]+)/$', member.bills, name='bills'),
     url(r'^memberships/(?P<username>[^/]+)/$', member.membership, name='memberships'),
     url(r'^files/(?P<username>[^/]+)/$', member.files, name='files'),

     # TODO remove
     # url(r'^signins/(?P<username>[^/]+)/$', member.signins, name='user_signins'),
     # url(r'^signins/json/(?P<username>[^/]+)/$', member.signins_json, name='json_signins'),
     # url(r'^edit/(?P<username>[^/]+)/$', member.edit, name='user_edit'),

]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
