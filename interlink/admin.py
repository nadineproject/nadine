from django.contrib import admin
from django import forms
from django.forms.util import ErrorList
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from models import MailingList, IncomingMail, OutgoingMail

class MailingListAdmin(admin.ModelAdmin):
   pass
admin.site.register(MailingList, MailingListAdmin)

class IncomingMailAdmin(admin.ModelAdmin):
   list_display = ('sent_time', 'origin_address', 'subject')
admin.site.register(IncomingMail, IncomingMailAdmin)

class OutgoingMailAdmin(admin.ModelAdmin):
   list_display = ('id', 'original_mail', 'subject', 'sent')
admin.site.register(OutgoingMail, OutgoingMailAdmin)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
