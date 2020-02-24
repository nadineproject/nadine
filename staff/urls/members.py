from django.urls import path

from staff.views import members
#from staff.views import stripe


app_name = 'staff'
urlpatterns = [
     path('members/', members.members, name='members'),
     path('members/<group>/', members.members, name='member_group'),
     path('bcc/', members.bcc_tool, name='bcc_tool'),
     path('bcc/<group>/', members.bcc_tool, name='group_bcc'),
     path('deposits/', members.security_deposits, name='deposits'),
     path('export/', members.export_users, name='export_users'),
     path('search/', members.member_search, name='search'),
     path('new_user/', members.new_user, name='new_user'),
     path('user_reports/', members.view_user_reports, name='user_reports'),
     path('slack_users/', members.slack_users, name='slack_users'),
     path('membership/<username>/', members.membership, name='membership'),
     path('confirm/<username>/<package>/<end_target>/<start_target>/<new_subs>/', members.confirm_membership, name='confirm'),
     path('edit_bill_day/<username>/', members.edit_bill_day, name='edit_bill_day'),
     path('organizations/', members.org_list, name='organizations'),
     path('organization/<int:org_id>/', members.org_view, name='organization'),
     path('files/<username>/', members.files, name='files'),
     path('detail/<username>/', members.detail, name='detail'),
     #path('detail/<username>/stripe/', stripe.Checkout.as_view(), name='stripe-checkout'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
