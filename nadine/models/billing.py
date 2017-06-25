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

from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.resource import Resource
from nadine.models.usage import CoworkingDay

logger = logging.getLogger(__name__)

class BatchManager(models.Manager):

    def run(self, start_date=None, end_date=None):
        batch = self.create()
        if batch.run(start_date, end_date):
            return batch
        else:
            raise Exception(batch.error)

class BillingBatch(models.Model):
    """Gathers all untracked subscriptions and activity and associates it with a UserBill."""
    objects = BatchManager()
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    completed_ts = models.DateTimeField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    bills = models.ManyToManyField('UserBill')

    class Meta:
        app_label = 'nadine'
        ordering = ['-created_ts']
        get_latest_by = 'created_ts'

    def __unicode__(self):
        return 'BillingBatch %s: %s' % (self.created_ts, self.successful)

    @property
    def successful(self):
        return self.error == None

    def save_bill(self, bill):
        if bill not in self.bills.all():
            self.bills.add(bill)
            self.save()

    def run(self, start_date=None, end_date=None):
        ''' Run billing for every day since the last successful billing run. '''
        logger.info("run(start_date=%s, end_date=%s)" % (start_date, end_date))
        try:
            # Make sure no other batches are running
            if BillingBatch.objects.filter(completed_ts=None).exclude(id=self.id).count() > 0:
                raise Exception("Found a BillingBatch that has not yet completed!")

            # If no end_date, go until today
            if not end_date:
                end_date = localtime(now()).date()

            # If no start_date, start from the last successful batch run
            target_date = start_date
            if not target_date:
                last_batch = BillingBatch.objects.filter(error__isnull=True).order_by('created_ts').last()
                target_date = last_batch.created_ts.date()

            # Run for each day in our range
            while target_date <= end_date:
                self.run_billing_for_day(target_date)
                target_date = target_date + timedelta(days=1)
        except Exception as e:
            # Save all error messages
            self.error = str(e)
            logger.error(self.error)
        finally:
            self.completed_ts = localtime(now())
            self.save()
        # Indicate if we ran successsfully or not
        return self.successful

    def run_billing_for_day(self, target_date):
        ''' Run billing for a specific day. '''
        logger.info("run_billing_for_day(%s)" % target_date)

        # Check every active subscription on this day and add this if neccessary
        for subscription in ResourceSubscription.objects.unbilled(target_date):
            # Find the open bill for the membership period of this subscription
            period_start, period_end = subscription.membership.get_period(target_date)
            bill = UserBill.objects.get_or_create_open_bill(subscription.payer, period_start, period_end)
            if not bill.has_subscription(subscription):
                bill.add_subscription(subscription)
                self.save_bill(bill)

        # Pull and add all past unbilled CoworkingDays
        for day in CoworkingDay.objects.unbilled(target_date):
            # Find the open bill for the period of this one day
            bill = UserBill.objects.get_or_create_open_bill(day.payer, day.visit_date, day.visit_date)
            bill.add_coworking_day(day)
            self.save_bill(bill)

        # Close all open bills that end on this day
        for bill in UserBill.objects.filter(closed_ts__isnull=True, period_end=target_date):
            bill.close()
            self.save_bill(bill)


class BillManager(models.Manager):

    def get_open_bill(self, user, period_start, period_end):
        ''' Get one and only one open UserBill for a given user and period. '''
        bills = self.filter(
            user = user,
            period_start__lte = period_start,
            period_end__gte = period_end,
            closed_ts__isnull = True,
        )

        # One and only one bill
        if bills.count() > 1:
            raise Exception("Found more than one bill!")

        # Returns the one or None if we didn't find anything
        return bills.first()

    def get_or_create_open_bill(self, user, period_start, period_end):
        ''' Get or create a UserBill for the given ResourceSubscription and date. '''
        bill = UserBill.objects.get_open_bill(user, period_start, period_end)
        if bill:
            return bill

        # If there is no bill for this specific period, find any open bill
        last_open_bill = UserBill.objects.filter(user=user, closed_ts__isnull=True).order_by('due_date').last()
        if last_open_bill:
            # Expand the period to include this visit
            if last_open_bill.period_start > period_start:
                last_open_bill.period_start = period_start
            if last_open_bill.period_end < period_end:
                last_open_bill.period_end = period_end
            last_open_bill.save()
            return last_open_bill

        # Create a new UserBill
        if not bill:
            bill = UserBill.objects.create(
                user = user,
                period_start = period_start,
                period_end = period_end,
                due_date = period_end,
            )
        return bill

    def create_for_day(self, user, target_date=None):
        ''' Create a UserBill for the given user for one day only. '''
        if not target_date:
            target_date = localtime(now()).date()
        bill = UserBill.objects.create(
            user = user,
            period_start = target_date,
            period_end = target_date,
            due_date = target_date,
        )
        return bill

    def open(self):
        return self.filter(closed_ts__isnull=True)

    def closed(self):
        return self.filter(closed_ts__isnull=False)

    def unpaid(self, user=None, in_progress=None):
        # TODO - should take no arguments
        query = self.filter(mark_paid=False)
        if user != None:
            query = query.filter(user=user)
        if in_progress != None:
            query = query.filter(in_progress=in_progress)
        query = query.annotate(bill_amount=Sum('line_items__amount'), owed=Sum('line_items__amount') - Sum('payment__amount'), payment_count=Count('payment'))
        no_payments = Q(payment_count = 0)
        partial_payment = Q(owed__gt = 0)
        query = query.filter(bill_amount__gt=0).filter(no_payments | partial_payment)
        return query.order_by('due_date')

    def non_zero(self):
        return self.annotate(bill_amount=Sum('line_items__amount')).filter(bill_amount__gt=0)


class UserBill(models.Model):
    objects = BillManager()
    created_ts = models.DateTimeField(auto_now_add=True)
    closed_ts = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bills", on_delete=models.CASCADE)
    # membership = models.ForeignKey(Membership, related_name="bills", null=True, blank=True, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    comment = models.TextField(blank=True, null=True, help_text="Public comments visable by the user")
    note = models.TextField(blank=True, null=True, help_text="Private notes about this bill")
    in_progress = models.BooleanField(default=False, blank=False, null=False, help_text="Mark a bill as 'in progress' indicating someone is working on it")
    mark_paid = models.BooleanField(default=False, blank=False, null=False, help_text="Mark a bill as paid even if it is not")

    def __unicode__(self):
        return "Bill %d" % self.id

    ############################################################################
    # Properties
    ############################################################################

    @property
    def total_paid(self):
        return self.payment_set.aggregate(paid=Coalesce(Sum('amount'), Value(0.00)))['paid']

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

    @property
    def package_name(self):
        if self.membership:
            return self.membership.package_name(self.period_start)

    @property
    def monthly_rate(self):
        if self.membership:
            return self.membership.monthly_rate(self.period_start)

    @property
    def overage_amount(self):
        if self.monthly_rate:
            if self.amount < self.monthly_rate:
                return 0
            else:
                return self.amount - self.monthly_rate

    @property
    def is_open(self):
        return self.closed_ts == None

    @property
    def is_closed(self):
        return self.closed_ts != None

    ############################################################################
    # URL Methods
    ############################################################################

    def get_absolute_url(self):
        return reverse('member:receipt', kwargs={'bill_id': self.id})

    def get_regenerate_url(self):
        if not self.membership:
            return None
        kwargs={
            'membership_id': self.membership.id,
            'year': self.period_start.year,
            'month': self.period_start.month,
            'day': self.period_start.day,
        }
        return reverse('staff:billing:generate_bills', kwargs=kwargs)

    def get_staff_url(self):
        return reverse('staff:billing:bill', kwargs={'bill_id': self.id})

    def get_admin_url(self):
        return reverse('admin:nadine_userbill_change', args=[self.id])

    ############################################################################
    # Other Methods
    ############################################################################

    def subscriptions(self):
        ''' Return all the ResourceSubscriptions associated with this bill. '''
        subscription_ids = SubscriptionLineItem.objects.filter(bill=self).values('subscription')
        return ResourceSubscription.objects.filter(id__in=subscription_ids)

    def has_subscription(self, subscription):
        ''' Return True if the given subscription is in the line items. '''
        return subscription in self.subscriptions()

    def add_subscription(self, subscription):
        ''' Create a line item for this ResourceSubscription. '''
        if self.has_subscription(subscription):
            return

        # Start with a generic description
        description = "Monthly " + subscription.resource.name + " "

        # If there is already a description on the subscription, add that
        if subscription.description:
            description += subscription.description + " "

        # If the subscription period falls outside this bill period,
        # add the date range to the description
        started_after = subscription.start_date > self.period_start
        ended_before = subscription.end_date and subscription.end_date < self.period_start
        ended_during = subscription.end_date and subscription.end_date < self.period_end
        if started_after or ended_before or ended_during:
            description += "(%s to %s)" % (self.period_start, self.period_end)

        # Calculate our amount
        prorate = subscription.prorate_for_period(self.period_start, self.period_end)
        amount = prorate * subscription.monthly_rate

        # Create our new line item
        return SubscriptionLineItem.objects.create(
            bill = self,
            subscription = subscription,
            description = description,
            amount = amount
        )

    def coworking_days(self):
        ''' Return all CoworkingDays associated with this bill. '''
        day_ids = CoworkingDayLineItem.objects.filter(bill=self).values('day')
        return CoworkingDay.objects.filter(id__in=day_ids)

    def has_coworking_day(self, coworking_day):
        ''' Return True if the given day is in the line items. '''
        return coworking_day in self.coworking_days()

    def add_coworking_day(self, day):
        resource = Resource.objects.day_resource
        allowance = self.resource_allowance(resource)
        overage_rate = self.resource_overage_rate(resource)

        # Start building our description
        description = "%s %s" % (resource.name, day.visit_date)

        amount = 0
        if day.billable:
            billable_count = CoworkingDay.objects.billable().filter(bill=self).count() + 1
            if billable_count > allowance:
                amount = overage_rate
            description += " (%d) " % billable_count
        else:
            # Indicate why this isn't billed
            description += " (%s) " % day.payment

        # Append the username if it's different from this bill
        if day.user != self.user:
            description += " for " + day.user.username

        # Create the line item
        line_item = CoworkingDayLineItem.objects.create(
            bill = self,
            description = description,
            amount = amount,
            day = day,
        )

        # Add a link back to this UserBill from the CoworkingDay
        day.bill = self
        day.save()

        return line_item

    def resource_allowance(self, resource):
        ''' Add up all the allowances to see how much activity is allowed. '''
        allowance = 0
        subscriptions = self.subscriptions().filter(resource=resource)
        for s in subscriptions:
            allowance += s.allowance
        return allowance

    def resource_overage_rate(self, resource):
        # Assume the overage rate for all subscriptions is the same.
        # This will cause problems if there are multiple subscriptions with different rates!!!
        # But since this should not be the case 99% of the time I'm going to do it the simple way --JLS
        subscriptions = self.subscriptions().filter(resource=resource)
        if not subscriptions:
            return resource.default_rate
        return subscriptions.first().overage_rate

    def close(self):
        if self.closed_ts != None:
            raise Exception("Bill is already closed!")
        self.closed_ts = localtime(now())
        self.save()


class BillLineItem(models.Model):
    bill = models.ForeignKey(UserBill, related_name="line_items", null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    custom = models.BooleanField(default=False)

    def __unicode__(self):
        return self.description


class SubscriptionLineItem(BillLineItem):
    subscription = models.ForeignKey('ResourceSubscription', related_name="line_items", on_delete=models.CASCADE)


class CoworkingDayLineItem(BillLineItem):
    day = models.ForeignKey('CoworkingDay', related_name="line_items", on_delete=models.CASCADE)


class Payment(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    bill = models.ForeignKey(UserBill, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True, help_text="Private notes about this payment")

    def __unicode__(self):
        return "%s: %s - $%s" % (str(self.created_ts)[:16], self.user, self.amount)
