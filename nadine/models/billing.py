import logging
from decimal import Decimal
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import F, Q, Count, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

from nadine.models.membership import Membership
from nadine.models.resource import Resource

logger = logging.getLogger(__name__)

class BillManager(models.Manager):

    def unpaid(self, user=None, in_progress=None):
        query = self.filter(mark_paid=False)
        if user != None:
            query = query.filter(user=user)
        if in_progress != None:
            query = query.filter(in_progress=in_progress)
        query = query.annotate(owed=Sum('line_items__amount') - Sum('payment__paid_amount'), payment_count=Count('payment'))
        no_payments = Q(payment_count = 0)
        partial_payment = Q(owed__gt = 0)
        query = query.filter(no_payments | partial_payment)
        return query.order_by('due_date')


class UserBill(models.Model):
    objects = BillManager()
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bills", on_delete=models.CASCADE)
    membership = models.ForeignKey(Membership, related_name="bills", null=True, blank=True, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    comment = models.TextField(blank=True, null=True)
    in_progress = models.BooleanField(default=False, blank=False, null=False)
    mark_paid = models.BooleanField(default=False, blank=False, null=False)

    def __unicode__(self):
        return "Bill %d" % self.id

    @property
    def total_paid(self):
        return self.payment_set.aggregate(paid=Coalesce(Sum('paid_amount'), Value(0.00)))['paid']

    @property
    def total_owed(self):
        return self.amount - self.total_paid

    @property
    def amount(self):
        return self.line_items.aggregate(amount=Coalesce(Sum('amount'), Value(0.00)))['amount']

    @property
    def is_paid(self):
        return self.mark_paid or self.total_owed <= 0

    @property
    def payment_date(self):
        # Date of the last payment
        last_payment = self.payments.order_by('payment_date').last()
        if last_payment:
            return last_payment.payment_date
        else:
            return None

    def get_absolute_url(self):
        return reverse('member:receipt', kwargs={'bill_id': self.id})

    def get_staff_url(self):
        return reverse('staff:billing:bill', kwargs={'bill_id': self.id})

    def get_admin_url(self):
        return reverse('admin:nadine_userbill_change', args=[self.id])

    def get_activity_period(self):
        # Activity period is the previous month
        activity_period_end = self.period_start - timedelta(days=1)
        activity_period_start = activity_period_end - relativedelta(months=1) + timedelta(days=1)
        return (activity_period_start, activity_period_end)

    def resource_allowance(self, resource):
        ''' Add up all the allowances to see how much activity is included in this membership. '''
        ps, pe = self.get_activity_period()
        subscriptions = self.membership.subscriptions_for_period(ps, pe).filter(resource=resource)
        if not subscriptions:
            return None
        allowance = 0
        for s in subscriptions:
            allowance += s.allowance
        return allowance

    def resource_overage_rate(self, resource):
        # Assume the overage rate for all subscriptions is the same.
        # This will cause problems if there are multiple subscriptions with different rates!!!
        # But since this should not be the case 99% of the time I'm going to do it the simple way --JLS
        ps, pe = self.get_activity_period()
        subscriptions = self.membership.subscriptions_for_period(ps, pe).filter(resource=resource)
        if not subscriptions:
            return None
        return subscriptions.first().overage_rate

    def resource_activity_count(self, resource):
        return self.line_items.filter(resource=resource).count()

    def resource_overage_count(self, resource):
        allowance = self.resource_allowance(resource)
        if allowance != None:
            activity_count = self.resource_activity_count(resource)
            if allowance < activity_count:
                return activity_count - allowance
            return 0

    def generate_monthly_line_item(self, subscription):
        desc = "Monthly " + subscription.resource.name + " "
        if subscription.description:
            desc += subscription.description + " "
        desc += "(%s to %s)" % (self.period_start, self.period_end)
        logger.debug("description: %s" % desc)
        prorate = subscription.prorate_for_period(self.period_start, self.period_end)
        logger.debug("prorate = %f" % prorate)
        amount = prorate * subscription.monthly_rate
        line_item = BillLineItem(bill=self, description=desc, amount=amount)
        return line_item

    def generate_activity_line_items(self, resource):
        ''' Generate line items for all activity for the given resource in the given period. '''
        period_start, period_end = self.get_activity_period()
        allowance = self.resource_allowance(resource)
        if allowance == None:
            # This indicates we have no subscriptions for this resource
            # TODO - wrong.  They could still have activity
            return
        overage_rate = self.resource_overage_rate(resource)
        user_list = self.membership.users_in_period(period_start, period_end)
        tracker = resource.get_tracker()

        line_items = []
        allowance_left = allowance
        for user in user_list:
            for activity in tracker.get_activity(user, period_start, period_end):
                activity_count = len(line_items) + 1
                description = "%s %s (%d)" % (activity.activity_date, resource.name, activity_count)
                amount = overage_rate
                if allowance_left > 0:
                    amount = 0
                    allowance_left = allowance_left - 1

                line_item = BillLineItem(
                    bill = self,
                    description = description,
                    amount = amount,
                    resource = resource,
                    activity_id = activity.id

                )

                line_items.append(line_item)

        if len(line_items) > 0:
            return line_items

    # Not sure if I need this -- JLS
    # def non_refund_payments(self):
    #     return self.payments.filter(paid_amount__gt=0)
    #
    # Not sure if we need this either if we create them in the right order
    # and pull them ordering by ID
    # def ordered_line_items(self):
    #     # return bill line items with custom items last
    #     # custom items, then the fees
    #     line_items = self.line_items.filter(custom=False)
    #     custom_items = self.line_items.filter(custom=True)
    #     return list(line_items) + list(custom_items)
    #
    # def delete_non_custom_items(self):
    #     for i in self.line_items.filter(custom=False):
    #         i.delete()


class BillLineItem(models.Model):
    bill = models.ForeignKey(UserBill, related_name="line_items", null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    resource = models.ForeignKey(Resource, blank=True, null=True, db_index=True, on_delete=models.CASCADE)
    activity_id = models.IntegerField(default=0)
    custom = models.BooleanField(default=False)

    def __unicode__(self):
        return self.description


#
# I don't think this is the right way to go -- JLS
# class CoworkingDayLineItem(BillLineItem):
#     days = models.ManyToManyField('CoworkingDay', related_name='bill_line')


class Payment(models.Model):
    bill = models.ForeignKey(UserBill, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_service = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Stripe, Paypal, Dwolla, etc. May be empty")
    payment_method = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Visa, cash, bank transfer")
    paid_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=200, null=True, blank=True)
    last4 = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return "%s: %s - $%s" % (str(self.payment_date)[:16], self.user, self.paid_amount)
