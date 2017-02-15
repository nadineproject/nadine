from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.payment import Transaction, Bill, BillingLog


class TransactionAdmin(StyledAdmin):
    list_display = ('transaction_date', 'user', 'amount')
    search_fields = ('user__first_name', 'user__last_name', 'amount')
    raw_id_fields = ('bills', 'user')
admin.site.register(Transaction, TransactionAdmin)


class BillAdmin(StyledAdmin):
    list_display = ('bill_date', 'user', 'amount')
    search_fields = ('user__first_name', 'user__last_name')
    raw_id_fields = ('membership', 'dropins', 'guest_dropins')
admin.site.register(Bill, BillAdmin)


class BillingLogAdmin(StyledAdmin):
    list_display = ('started', 'ended', 'note', 'successful')
admin.site.register(BillingLog, BillingLogAdmin)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
