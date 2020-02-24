from django.contrib import admin
from django import forms
from django.forms.utils import ErrorList
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin

from nadine.models.usage import CoworkingDay, Event

from nadine.admin.core import StyledAdmin


class EventAdmin(StyledAdmin):
    list_display = ('user', 'room', 'start_ts', 'end_ts', 'paid_by', 'created_ts')
    list_filter = ('is_public', )
    raw_id_fields = ('user', 'paid_by')
    search_fields = ('user__first_name', 'user__last_name', 'paid_by__first_name', 'paid_by__last_name')
admin.site.register(Event, EventAdmin)


class CoworkingDayAdmin(StyledAdmin):
    list_display = ('visit_date', 'user', 'paid_by', 'payment')
    raw_id_fields = ('user', 'paid_by')
    search_fields = ('user__first_name', 'user__last_name', 'paid_by__first_name', 'paid_by__last_name')
    list_filter = ('payment', )
    # Not neccessary since we went to a raw_id_field on paid_by
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "paid_by":
    #         kwargs["queryset"] = User.helper.active_members()
    #     return super(CoworkingDayAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
admin.site.register(CoworkingDay, CoworkingDayAdmin)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
