# -*- coding: utf-8 -*-
from django.contrib import admin
from comlink.models import IncomingEmail, Attachment, SimpleMailingList

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0

class EmailAdmin(admin.ModelAdmin):
    list_display = ('received', 'sender', 'recipient', 'subject')
    inlines = [AttachmentInline]
    readonly_fields = ('received',)

admin.site.register(IncomingEmail, EmailAdmin)
admin.site.register(Attachment)

class SimpleMailingListAdmin(admin.ModelAdmin):
    list_display = ('address', 'name', 'access_ts')
    raw_id_fields = ('subscribers', )
admin.site.register(SimpleMailingList, SimpleMailingListAdmin)
