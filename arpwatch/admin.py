from django.contrib import admin

from models import *

# Register the objects with the admin interface
admin.site.register(MACAddress)
admin.site.register(IPAddress)
admin.site.register(ArpLogEntry)
admin.site.register(ArpLog)
