import logging
from datetime import timedelta, date
from decimal import Decimal

from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from nadine.models.membership import Membership

logger = logging.getLogger(__name__)


class UserBill(models.Model):
    generated_on = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name="bill")
    period_start = models.DateField()
    period_end = models.DateField()
    # membership = models.ForeignKey(Membership, null=True)
    comment = models.TextField(blank=True, null=True)
    in_progress = models.BooleanField(default=False, blank=False, null=False)

    def __unicode__(self):
        return "Bill %d" % self.id

    def non_refund_payments(self):
        return self.payments.filter(paid_amount__gt=0)

    def total_paid(self):
        payments = self.payment_set.all()
        if not payments:
            return 0
        paid = Decimal(0)
        for payment in payments:
            paid = paid + payment.paid_amount
        return paid

    def total_owed(self):
        return self.amount() - self.total_paid()

    def amount(self):
        # Bill amount comes from generated bill line items
        amount = 0
        for line_item in self.line_items.all():
            amount = amount + line_item.amount
        return amount

    def is_paid(self):
        return self.total_owed() <= 0

    def payment_date(self):
        # Date of the last payment
        last_payment = self.payments.order_by('payment_date').reverse().first()
        if last_payment:
            return last_payment.payment_date
        else:
            return None

    def ordered_line_items(self):
        # return bill line items with custom items last
         # custom items, then the fees
        line_items = self.line_items.filter(custom=False)
        custom_items = self.line_items.filter(custom=True)
        return list(line_items) + list(custom_items)


class BillLineItem(models.Model):
    bill = models.ForeignKey(UserBill, related_name="line_items", null=True)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    custom = models.BooleanField(default=False)

    def __unicode__(self):
        return self.description


class CoworkingDayLineItem(BillLineItem):
    days = models.ManyToManyField('CoworkingDay', related_name='bill_line')


class Payment(models.Model):
    bill = models.ForeignKey(UserBill, null=True)
    user = models.ForeignKey(User, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_service = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Stripe, Paypal, Dwolla, etc. May be empty")
    payment_method = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Visa, cash, bank transfer")
    paid_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=200, null=True, blank=True)
    last4 = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "%s: %s - $%s" % (str(self.payment_date)[:16], self.user, self.paid_amount)
