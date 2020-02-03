from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.organization import Organization, OrganizationMember, OrganizationNote


class OrgMemberInline(admin.TabularInline):
    model = OrganizationMember
    raw_id_fields = ('user', )
    extra = 1


class OrgNoteInline(admin.TabularInline):
    model = OrganizationNote
    readonly_fields = ('created_by', 'created_ts', )
    extra = 1


class OrganizationAdmin(StyledAdmin):
    inlines = [OrgMemberInline, OrgNoteInline]
    search_fields = ('name', )
    readonly_fields = ('created_by', 'created_ts', )
    raw_id_fields = ('lead', )
    exclude = ('websites', )
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            instance.created_by = request.user
            instance.save()


admin.site.register(Organization, OrganizationAdmin)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
