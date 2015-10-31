from django.contrib import admin

from hid.models import *

class GatekeeperAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'accessed_ts', 'is_enabled')
    search_fields = ('ip_address', )
admin.site.register(Gatekeeper, GatekeeperAdmin)

admin.site.register(Door)
admin.site.register(DoorCode)

