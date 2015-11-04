from django.contrib import admin

from hid.models import *

class GatekeeperAdmin(admin.ModelAdmin):
    list_display = ('description', 'ip_address', 'access_ts', 'is_enabled')
    search_fields = ('ip_address', 'is_enabled')
admin.site.register(Gatekeeper, GatekeeperAdmin)

admin.site.register(Door)
admin.site.register(DoorCode)

