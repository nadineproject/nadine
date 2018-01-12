from django.contrib import admin
from django.contrib.auth.models import User

from nadine.admin import EmailAddressInline, UserProfileInline, EmergencyContactInline, XeroContactInline, UserWithProfileAdmin
from ldap_sync.models import LDAPAccountStatus

class LDAPAccountStatusInline(admin.TabularInline):
    model = LDAPAccountStatus
    readonly_fields = ['synchronized', 'ldap_error_message', 'ldap_dn', ]
    can_delete = False

class LDAPUserWithProfileAdmin(UserWithProfileAdmin):
    inlines = [EmailAddressInline, UserProfileInline, EmergencyContactInline, XeroContactInline, LDAPAccountStatusInline]
    # list_display = ('username', 'email', 'date_joined', 'last_login')
    # ordering = ('-date_joined', 'username')
    # search_fields = ('username', 'first_name', 'last_name', 'emailaddress__email')
    # readonly_fields = ('last_login', 'date_joined')
    # fieldsets = (
    #     (None, {'fields': ('username', 'first_name', 'last_name',
    #         'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'password')}),
    # )

admin.site.unregister(User)
admin.site.register(User, LDAPUserWithProfileAdmin)