from django.urls import path

from member.views import connect

app_name = 'member'
urlpatterns = [
    path('notifications/', connect.notifications, name='notifications'),
    path('notifications/add/<username>/', connect.add_notification, name='add_notification'),
    path('notifications/delete/<username>/', connect.delete_notification, name='del_notification'),
    path('chat/', connect.chat, name='chat'),
    path('lists/', connect.mail, name='email_lists'),
    path('mail/<id>/', connect.mail_message, name='view_mail'),
    path('slack/', connect.slack_redirect, name='slack_redirect'),
    path('slack/<username>/', connect.slack, name='slack'),
    path('slack_bots/', connect.slack_bots, name='slack_bot'),
    path('<username>)/', connect.connect, name='connect'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
