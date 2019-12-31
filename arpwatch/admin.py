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


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
