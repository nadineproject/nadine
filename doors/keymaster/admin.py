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

