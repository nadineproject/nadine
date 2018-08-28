from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.billing import BillingBatch, UserBill, BillLineItem
from nadine.models.billing import Payment, PaymentMethod
from nadine.models.billing import TaxRate, LineItemTax


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    extra = 0

# class LineItemTaxInline(admin.TabularInline):
#     model = LineItemTax
#     extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    raw_id_fields = ('user', )
    # For now let's just make this read-only
    readonly_fields = ('user', 'amount', 'method', 'note')
    fields = (('user', 'amount'), 'method', 'note')
    extra = 0
    # TODO = Hardcode user to be the bill.user

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Hardcode created_by top be request.user
        if db_field.name == 'created_by':
            kwargs['initial'] = request.user.username
            return db_field.formfield(**kwargs)

        return super(PaymentInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class UserBillAdmin(StyledAdmin):
    model = UserBill
    list_display = ('id', 'user', 'period_start', 'period_end', 'amount', 'tax_amount', 'total', 'total_paid')
    search_fields = ('user__username', 'user__first_name')
    raw_id_fields = ('user', )
    readonly_fields = ('id', 'created_ts', )
    fields = (
        ('id', 'created_ts', 'closed_ts'),
        ('due_date', 'period_start', 'period_end'),
        'user',
        'in_progress',
        'mark_paid',
        'comment',
        'note',
    )
    ordering = ['-period_start', ]
    inlines = [BillLineItemInline, PaymentInline]


class PaymentMethodAdmin(StyledAdmin):
    model = PaymentMethod


class LineItemTaxAdmin(StyledAdmin):
    model = LineItemTax


class TaxRateAdmin(StyledAdmin):
    model = TaxRate


class BillingBatchAdmin(StyledAdmin):
    def bills(self):
        return self.bills.count()

    model = BillingBatch
    date_hierarchy = 'created_ts'
    list_display = ('id', 'created_by', 'created_ts', 'completed_ts', 'successful', bills)
    fields = ('id', bills, 'created_ts', 'completed_ts', 'created_by', 'error')
    readonly_fields = ('id', bills, 'created_ts', 'created_by', 'completed_ts', 'error')


admin.site.register(BillingBatch, BillingBatchAdmin)
admin.site.register(UserBill, UserBillAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(TaxRate, TaxRateAdmin)
admin.site.register(LineItemTax, LineItemTaxAdmin)
