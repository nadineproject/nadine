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


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
