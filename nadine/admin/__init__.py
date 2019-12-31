from django.contrib import admin
from django import forms
from django.forms.utils import ErrorList
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

from nadine.models import *

from nadine.admin.core import StyledAdmin
from nadine.admin.user import *
from nadine.admin.organization import *
from nadine.admin.billing import *
from nadine.admin.membership import *
from nadine.admin.usage import *


# Register the objects with the admin interface
admin.site.register(Neighborhood)
admin.site.register(Industry)
admin.site.register(HowHeard)
admin.site.register(Room)
admin.site.register(Resource)


class SentEmailLogAdmin(StyledAdmin):
    list_display = ('created', 'recipient', 'subject', 'note', 'success')
admin.site.register(SentEmailLog, SentEmailLogAdmin)


class SpecialDayAdmin(StyledAdmin):
    list_display = ('user', 'year', 'month', 'day', 'description')
admin.site.register(SpecialDay, SpecialDayAdmin)


class MemberNoteAdmin(StyledAdmin):
    list_display = ('created', 'user', 'created_by', 'note')
admin.site.register(MemberNote, MemberNoteAdmin)


class MemberAlertAdmin(StyledAdmin):
    def unresolve(self, request, queryset):
        for alert in queryset:
            alert.resolved_ts = None
            alert.resolved_by = None
            alert.muted_ts = None
            alert.muted_by = None
            alert.save()
        self.message_user(request, "Alerts Unresolved")

    list_display = ('created_ts', 'key', 'user', 'resolved_ts', 'resolved_by', 'muted_ts', 'muted_by', 'note')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('key', )
    actions = ["unresolve", ]
admin.site.register(MemberAlert, MemberAlertAdmin)


class FileUploadAdmin(StyledAdmin):
    list_display = ('uploadTS', 'user', 'name')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('document_type',)
admin.site.register(FileUpload, FileUploadAdmin)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
