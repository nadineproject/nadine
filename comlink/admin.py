# -*- coding: utf-8 -*-
from django.contrib import admin
from comlink.models import IncomingEmail, Attachment, MailingList

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0

class EmailAdmin(admin.ModelAdmin):
    list_display = ('received', 'sender', 'recipient', 'subject')
    inlines = [AttachmentInline]
    readonly_fields = ('received',)

admin.site.register(IncomingEmail, EmailAdmin)
admin.site.register(Attachment)

class MailingListAdmin(admin.ModelAdmin):
    list_display = ('address', 'name', 'access_ts')
    raw_id_fields = ('subscribers', )
admin.site.register(MailingList, MailingListAdmin)


# Copyright 2020Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
