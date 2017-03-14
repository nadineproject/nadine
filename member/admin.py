from django.contrib import admin

from members.models import *


class MOTDAdmin(admin.ModelAdmin):
    list_display = ('start_ts', 'end_ts', 'message', 'delay_ms')
admin.site.register(MOTD, MOTDAdmin)


class HelpTextAdmin(admin.ModelAdmin):
    pass
admin.site.register(HelpText, HelpTextAdmin)


class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('created', 'notify_user', 'target_user', 'sent_date')
admin.site.register(UserNotification, UserNotificationAdmin)
