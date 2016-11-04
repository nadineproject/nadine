from django.contrib import admin

from arpwatch.models import *

# Register the objects with the admin interface
admin.site.register(ImportLog)


class ArpLogAdmin(admin.ModelAdmin):
    list_display = ('runtime', 'device', 'ip_address')
    search_fields = ('ip_address', )
admin.site.register(ArpLog, ArpLogAdmin)


class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('mac_address', 'user', 'device_name', 'ignore')
    search_fields = ('mac_address', 'user__username')
    readonly_fields = ('last_seen', )
    raw_id_fields = ('user', )
admin.site.register(UserDevice, UserDeviceAdmin)


class UserRemoteAddrAdmin(admin.ModelAdmin):
    list_display = ('logintime', 'user', 'ip_address')
    search_fields = ('ip_address', 'user__username')
admin.site.register(UserRemoteAddr, UserRemoteAddrAdmin)
