# -*- coding: utf-8 -*-
from django.contrib import admin
from comlink.models import IncomingEmail, Attachment

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0

class EmailAdmin(admin.ModelAdmin):
    inlines = [AttachmentInline]
    readonly_fields = ('received',)

admin.site.register(IncomingEmail, EmailAdmin)
admin.site.register(Attachment)
