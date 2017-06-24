from django.contrib import admin

from nadine.admin.core import StyledAdmin
from nadine.models.billing import UserBill, Payment, BillLineItem


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    extra = 0

class PaymentInline(admin.TabularInline):
    model = Payment
    raw_id_fields = ('user', )
    # For now let's just make this read-only
    readonly_fields = ('user', 'amount', 'note')
    fields = (('user', 'amount'), 'note')
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
    list_display = ('id', 'user', 'period_start', 'period_end', 'amount', 'total_paid')
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


admin.site.register(UserBill, UserBillAdmin)
