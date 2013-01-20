from django.contrib import admin

from models import *

# Register the objects with the admin interface
admin.site.register(ArpLog)
admin.site.register(UserDevice)
admin.site.register(ImportLog)
admin.site.register(UserRemoteAddr)
