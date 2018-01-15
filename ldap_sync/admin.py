from django.contrib import admin
from django.contrib.auth.models import User

from nadine.admin import EmailAddressInline, UserProfileInline, EmergencyContactInline, XeroContactInline, UserWithProfileAdmin
from ldap_sync.models import LDAPAccountStatus

class LDAPAccountStatusInline(admin.TabularInline):
    """
    Defines admin widget for LDAPAccountStatus information.
    """
    model = LDAPAccountStatus
    readonly_fields = ['synchronized', 'ldap_uid', 'ldap_dn', 'ldap_error_message',]
    can_delete = False

class LDAPUserWithProfileAdmin(UserWithProfileAdmin):
    """
    Extends existing user profile admin with LDAPAccountStatus info.
    """
    inlines = [EmailAddressInline, UserProfileInline, EmergencyContactInline, XeroContactInline, LDAPAccountStatusInline]

admin.site.unregister(User)
admin.site.register(User, LDAPUserWithProfileAdmin)