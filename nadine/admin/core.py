from django.contrib import admin


class StyledAdmin(admin.ModelAdmin):

    class Media:
        css = {"all": ('local-admin.css', )}
