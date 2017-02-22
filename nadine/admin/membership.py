from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.membership import Membership, ResourceSubscription, SecurityDeposit


class SubscriptionInline(admin.TabularInline):
    model = ResourceSubscription
    extra = 1


class MembershipAdmin(StyledAdmin):

    def active_subscriptions(self):
        return self.active_subscriptions().count()

    def next_bill(self):
        return self.next_period_start()

    inlines = [SubscriptionInline, ]
    list_display = ('id', 'who', 'bill_day', next_bill, active_subscriptions)
    fields = ['bill_day']
    list_select_related = ('individualmembership', 'organizationmembership')
    search_fields = ('individualmembership__user__username', 'organizationmembership__organization__name')
admin.site.register(Membership, MembershipAdmin)


class SecurityDepositAdmin(StyledAdmin):
    list_display = ('user', 'received_date', 'returned_date', 'amount', 'note')
admin.site.register(SecurityDeposit, SecurityDepositAdmin)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
