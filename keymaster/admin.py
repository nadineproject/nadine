from django.contrib import admin

from keymaster.models import *

class GatekeeperAdmin(admin.ModelAdmin):
    def force_sync(self, request, queryset):
        for gk in queryset:
            gk.force_sync()
        self.message_user(request, "Sync will be forced on next contact from the gatekeeper")
    list_display = ('description', 'ip_address', 'access_ts', 'sync_ts', 'is_enabled')
    search_fields = ('ip_address', 'is_enabled')
    actions = ["force_sync", ]
admin.site.register(Gatekeeper, GatekeeperAdmin)

admin.site.register(Door)
admin.site.register(DoorCode)

