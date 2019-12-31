from django.contrib import admin

from doors.keymaster.models import *

class KeymasterAdmin(admin.ModelAdmin):
    def force_sync(self, request, queryset):
        for km in queryset:
            km.force_sync()
        self.message_user(request, "Sync will be forced on next contact from the gatekeeper")

    list_display = ('description', 'gatekeeper_ip', 'access_ts', 'success_ts', 'sync_ts', 'is_enabled')
    search_fields = ('gatekeeper_ip', 'is_enabled')
    actions = ["force_sync", ]

class DoorEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'door', 'event_type', 'user', 'code', 'event_description', )
    list_filter = ('door', 'event_type', )
    search_fields = ('user', 'code')
    ordering = ['-timestamp']

admin.site.register(Keymaster, KeymasterAdmin)
admin.site.register(DoorEvent, DoorEventAdmin)
admin.site.register(Door)
admin.site.register(DoorCode)
admin.site.register(GatekeeperLog)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
