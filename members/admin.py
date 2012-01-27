from django.contrib import admin

from models import HelpText

class HelpTextAdmin(admin.ModelAdmin):
	pass
admin.site.register(HelpText, HelpTextAdmin)
