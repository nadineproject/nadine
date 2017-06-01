from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.billing import UserBill, Payment, BillLineItem


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    extra = 0


class UserBillAdmin(StyledAdmin):
    model = UserBill
    list_display = ('id', 'user', 'period_start', 'period_end', 'amount', 'total_paid')
    search_fields = ('user__username', 'user__first_name')
    raw_id_fields = ('user', )
    readonly_fields = ('id', 'created_ts', 'created_by')
    fields = ('id', 'user', 'created_ts', 'period_start', 'period_end', 'due_date')
    ordering = ['-period_start', ]
    inlines = [BillLineItemInline, PaymentInline]


admin.site.register(UserBill, UserBillAdmin)
