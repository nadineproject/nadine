from django.contrib import admin
from django import forms
from django.forms.util import ErrorList
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from nadine.models import *

# Register the objects with the admin interface
admin.site.register(Onboard_Task)
admin.site.register(Onboard_Task_Completed)
admin.site.register(ExitTask)
admin.site.register(Neighborhood)
admin.site.register(Industry)
admin.site.register(HowHeard)
admin.site.register(MembershipPlan)

class StyledAdmin(admin.ModelAdmin):
	class Media:
		css = { "all": ('local-admin.css', )}

class TransactionAdmin(StyledAdmin):
	list_display = ('transaction_date', 'member', 'amount')
	search_fields = ('member__user__first_name', 'member__user__last_name', 'amount')
	raw_id_fields = ('bills', 'member')
admin.site.register(Transaction, TransactionAdmin)

class BillAdmin(StyledAdmin):
	list_display = ('bill_date', 'member', 'amount')
	search_fields = ('member__user__first_name', 'member__user__last_name')
	raw_id_fields = ('membership', 'dropins', 'guest_dropins')
admin.site.register(Bill, BillAdmin)

class BillingLogAdmin(StyledAdmin):
	list_display = ('started', 'ended', 'note', 'successful')
admin.site.register(BillingLog, BillingLogAdmin)

admin.site.unregister(User)
class MemberInline(admin.StackedInline):
	model = Member
	max_num = 1
class UserWithProfileAdmin(UserAdmin):
	inlines = [MemberInline]
admin.site.register(User, UserWithProfileAdmin)

class DailyLogAdmin(StyledAdmin):
	list_display = ('visit_date', 'member', 'guest_of', 'created')
	search_fields = ('member__user__first_name', 'member__user__last_name', 'guest_of__user__first_name', 'guest_of__user__last_name')
admin.site.register(DailyLog, DailyLogAdmin)

class MembershipAdmin(StyledAdmin):
	list_display = ('member', 'start_date', 'end_date')
	search_fields = ('member__user__first_name', 'member__user__last_name')
admin.site.register(Membership, MembershipAdmin)

class SentEmailLogAdmin(StyledAdmin):
	list_display=('created', 'recipient', 'subject', 'note', 'success')
admin.site.register(SentEmailLog, SentEmailLogAdmin)

class SecurityDepositAdmin(StyledAdmin):
	list_display=('member', 'received_date', 'returned_date', 'amount', 'note')
admin.site.register(SecurityDeposit, SecurityDepositAdmin)
	
class SpecialDayAdmin(StyledAdmin):
	list_display=('member', 'year', 'month', 'day', 'description')
admin.site.register(SpecialDay, SpecialDayAdmin)
	
class MemberNoteAdmin(StyledAdmin):
	list_display=('created', 'member', 'created_by', 'note')
admin.site.register(MemberNote, MemberNoteAdmin)

class MemberAlertAdmin(StyledAdmin):
	list_display=('created_ts', 'key', 'user', 'resolved_ts', 'resolved_by', 'muted_ts', 'muted_by', 'note')
	search_fields = ('user__username', 'user__first_name', 'user__last_name')
	list_filter=('key', )
admin.site.register(MemberAlert, MemberAlertAdmin)

class FileUploadAdmin(StyledAdmin):
	list_display=('uploadTS', 'user', 'name')
admin.site.register(FileUpload, FileUploadAdmin)

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

