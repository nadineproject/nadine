from django.contrib import admin
from django.utils.timezone import localtime, now

from nadine.admin.core import StyledAdmin
from nadine.models.membership import Membership, ResourceSubscription, SecurityDeposit, MembershipPackage, SubscriptionDefault
from nadine.models.billing import UserBill


class DefaultInline(admin.StackedInline):
    model = SubscriptionDefault
    fields = [
        ('resource', 'allowance', 'monthly_rate', 'overage_rate'),
    ]
    extra = 1


class MembershipPackageAdmin(StyledAdmin):
    inlines = [DefaultInline, ]

admin.site.register(MembershipPackage, MembershipPackageAdmin)


class ActiveFilter(admin.SimpleListFilter):
    title = "is_active"
    parameter_name = "is_active"

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Yes':
            return queryset.exclude(address_line1__exact='').exclude(city__exact='').exclude(state__exact='').exclude(zip_code__exact='')
        if self.value() == 'No':
            return queryset.filter(Q(address_line1="") | Q(city="") | Q(state="") | Q(zip_code=""))


class SubscriptionInline(admin.StackedInline):
    model = ResourceSubscription
    readonly_fields = ('is_active', )
    fields = [
        ('resource', 'start_date', 'end_date'),
        ('package_name'),
        ('allowance', 'monthly_rate', 'overage_rate'),
        ('description', 'paid_by', 'is_active'),
    ]
    ordering = ['-start_date', '-created_ts']
    extra = 1


class MembershipAdmin(StyledAdmin):

    def active_subscriptions(self):
        return self.active_subscriptions().count()

    def next_bill(self):
        return self.next_period_start()

    def end_membership_yesterday(self, request, queryset):
        for m in queryset:
            try:
                m.end_all()
                self.message_user(request, "membership ended")
            except Exception as e:
                self.message_user(request, e)

    def end_membership_at_period_end(self, request, queryset):
        for m in queryset:
            try:
                m.end_at_period_end()
                self.message_user(request, "membership ended")
            except Exception as e:
                self.message_user(request, e)

    inlines = [SubscriptionInline, ]
    list_display = ('id', 'who', 'bill_day', next_bill, active_subscriptions)
    readonly_fields = ['who']
    fields = ['who', 'bill_day']
    list_select_related = ('individualmembership', 'organizationmembership')
    search_fields = ('individualmembership__user__username', 'organizationmembership__organization__name')
    actions= ['end_membership_yesterday', 'end_membership_at_period_end']

admin.site.register(Membership, MembershipAdmin)


class SecurityDepositAdmin(StyledAdmin):
    list_display = ('user', 'received_date', 'returned_date', 'amount', 'note')
admin.site.register(SecurityDeposit, SecurityDepositAdmin)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
