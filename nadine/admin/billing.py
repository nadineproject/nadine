from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.billing import UserBill, Payment, BillLineItem


class UserBillAdmin(StyledAdmin):
    model = UserBill
    list_display = ('id', 'user', 'period_start', 'period_end', 'amount', 'total_paid')
    search_fields = ('user__username', 'user__first_name')
    readonly_fields = ('generated_on', )
    fields = ('user', 'generated_on', 'period_start', 'period_end')
    ordering = ['-period_start', ]


class PaymentAdmin(StyledAdmin):
    model = Payment
    list_display = ('payment_date', 'user', 'payment_method', 'paid_amount')
    list_filter = ('payment_method', )
    ordering = ['-payment_date']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class BillLineItemAdmin(StyledAdmin):
    list_display = ('id', 'description', 'amount')


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    fields = ('description', 'amount', 'custom')
    extra = 0


class UserBillInline(admin.StackedInline):
    model = UserBill
    extra = 0
    inlines = [BillLineItemInline, PaymentInline]


admin.site.register(UserBill, UserBillAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(BillLineItem, BillLineItemAdmin)
