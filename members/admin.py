from django.contrib import admin

from models import *	


class HelpTextAdmin(admin.ModelAdmin):
	pass
admin.site.register(HelpText, HelpTextAdmin)

class UserNotificationAdmin(admin.ModelAdmin):
	list_display = ('created', 'notify_user', 'target_user', 'sent_date')
admin.site.register(UserNotification, UserNotificationAdmin)
