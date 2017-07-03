import logging
import traceback
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

    def run(self, start_date=None, end_date=None, created_by=None):
        batch = self.create(created_by=created_by)
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
        return self.completed_ts != None and self.error == None

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
            traceback.print_exc()
            logger.error(self.error)
        finally:
            self.completed_ts = localtime(now())
            self.save()
        # Indicate if we ran successsfully or not
        return self.successful

    def run_billing_for_day(self, target_date):
        ''' Run billing for a specific day. '''
        logger.info("run_billing_for_day(%s)" % target_date)

        # Keep track of which bills need to be recalculated
        to_recalculate = set()

        # Check every active subscription on this day and add this if neccessary
        for subscription in ResourceSubscription.objects.unbilled(target_date):
            logger.debug("Found Subscription: %s %s, %s to %s" % (subscription.membership.who, subscription.package_name, subscription.start_date, subscription.end_date))
            # Look at the membership of the payer to find the bill period
            membership = Membership.objects.for_user(subscription.payer)
            period_start, period_end = membership.get_period(target_date)
            if period_start is None:
                # If we did not get a period, the payer is not active on this date
                # Look instead at the membership for the individual
                membership = Membership.objects.for_user(subscription.user)
                period_start, period_end = membership.get_period(target_date)

            # Find the open bill for this period and add this subscription
            bill = UserBill.objects.get_or_create_open_bill(subscription.payer, period_start, period_end, check_open_bills=False)
            if not bill.has_subscription(subscription):
                bill.add_subscription(subscription)
                self.bills.add(bill)
                # If we have any activity for this resource, flag for recalculation
                activity = bill.resource_activity(subscription.resource)
                if activity and activity.count() > 0:
                    to_recalculate.add(bill)

        # Pull and add all past unbilled CoworkingDays
        for day in CoworkingDay.objects.unbilled(target_date):
            logger.debug("Found Coworking Day: %s %s %s" % (day.user, day.visit_date, day.payment))
            # Find the open bill for the period of this one day
            bill = UserBill.objects.get_or_create_open_bill(day.payer, day.visit_date, day.visit_date)
            bill.add_coworking_day(day)
            self.bills.add(bill)

        # Recalculate all the bills that need it
        for bill in to_recalculate:
            bill.recalculate()

        # Close all open subscription based bills that end on this day
        for bill in UserBill.objects.filter(closed_ts__isnull=True, period_end=target_date):
            if bill.subscriptions().count() > 0:
                # Only close bills that have subscriptions.
                # Bills with only resource activity remain open until paid
                bill.close()
                self.bills.add(bill)


class BillManager(models.Manager):

    def get_open_bill(self, user, period_start, period_end):
        ''' Get one and only one open UserBill for a given user and period. '''
        logger.debug("get_open_bill(%s, %s, %s)" % (user, period_start, period_end))

        bills = self.filter(
            user = user,
            period_start__lte = period_start,
            period_end__gte = period_end,
            closed_ts__isnull = True,
        )

        # One and only one bill
        if bills.count() > 1:
            logger.info("get_open_bill(%s, %s, %s)" % (user, period_start, period_end))
            for bill in bills:
                logger.info("Found %s" % bill)
            raise Exception("Found more than one bill!")

        # Returns the one or None if we didn't find anything
        return bills.first()

    def get_or_create_open_bill(self, user, period_start, period_end, check_open_bills=True):
        ''' Get or create a UserBill for the given ResourceSubscription and date. '''
        logger.debug("get_or_create_open_bill(%s, %s, %s, %s)" % (user, period_start, period_end, check_open_bills))

        bill = self.get_open_bill(user, period_start, period_end)
        if bill:
            return bill

        # If there is no bill for this specific period, find any open bill
        if check_open_bills:
            last_open_bill = self.filter(user=user, closed_ts__isnull=True).order_by('due_date').last()
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
            bill = self.create(
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
        bill = self.create(
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

    def outstanding(self):
        query = self.filter(mark_paid=False)
        query = query.annotate(bill_amount=Sum('line_items__amount'), owed=Sum('line_items__amount') - Sum('payment__amount'), payment_count=Count('payment'))
        no_payments = Q(payment_count = 0)
        partial_payment = Q(owed__gt = 0)
        return query.filter(bill_amount__gt=0).filter(no_payments | partial_payment)

    def non_zero(self):
        return self.annotate(bill_amount=Sum('line_items__amount')).filter(bill_amount__gt=0)


class UserBill(models.Model):
    objects = BillManager()
    created_ts = models.DateTimeField(auto_now_add=True)
    closed_ts = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="bills", on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    comment = models.TextField(blank=True, null=True, help_text="Public comments visable by the user")
    note = models.TextField(blank=True, null=True, help_text="Private notes about this bill")
    in_progress = models.BooleanField(default=False, blank=False, null=False, help_text="Mark a bill as 'in progress' indicating someone is working on it")
    mark_paid = models.BooleanField(default=False, blank=False, null=False, help_text="Mark a bill as paid even if it is not")

    def __unicode__(self):
        return "UserBill %d: %s %s to %s for $%s" % (self.id, self.user, self.period_start, self.period_end, self.amount)

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
    def monthly_rate(self):
        ''' Add up all rates for all the subscriptions. '''
        return self.subscriptions().aggregate(rate=Coalesce(Sum('monthly_rate'), Value(0.00)))['rate']

    @property
    def overage_amount(self):
        ''' The difference between the month_rate and the amount. '''
        if self.monthly_rate:
            if self.amount < self.monthly_rate:
                return 0
            else:
                return self.amount - self.monthly_rate

    @property
    def package_name(self):
        ''' If all subscriptions have the same package_name we'll assume that name for this bill as well. '''
        package_name = None
        for s in self.subscriptions():
            if package_name:
                if s.package_name != package_name:
                    return None
            else:
                package_name = s.package_name
        return package_name

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

    def get_staff_url(self):
        return reverse('staff:billing:bill', kwargs={'bill_id': self.id})

    def get_admin_url(self):
        return reverse('admin:nadine_userbill_change', args=[self.id])

    ############################################################################
    # Resource Methods
    ############################################################################

    def resource_allowance(self, resource):
        ''' Look at the subscriptions added to this bill to determine the allowance for the given resource. '''
        return self.subscriptions().filter(resource=resource).aggregate(sum=Coalesce(Sum('allowance'), Value(0.00)))['sum']

    def resource_overage_rate(self, resource):
        ''' Look at the subscriptions added to this bill and determin the overage rate for the given resource. '''

        # Assume the overage rate for all subscriptions is the same.
        # This will cause problems if there are multiple subscriptions
        # with different rates!!! Since this should not be the case 99%
        # of the time I'm going to do it the simple way --JLS
        subscriptions = self.subscriptions().filter(resource=resource)
        if subscriptions:
            return subscriptions.first().overage_rate

        # No subscriptions means we'll use the default rate
        return resource.default_rate

    def resource_activity(self, resource):
        ''' Return all the activity for the given resource. '''
        if resource == Resource.objects.day_resource:
            return self.coworking_days()

    @property
    def desk_allowance(self):
        return self.resource_allowance(Resource.objects.desk_resource)

    @property
    def mail_allowance(self):
        return self.resource_allowance(Resource.objects.mail_resource)

    @property
    def key_allowance(self):
        return self.resource_allowance(Resource.objects.key_resource)

    ###########################################################################
    # Subscription Methods
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
        description = ""
        if subscription.package_name:
            description = subscription.package_name + " "
        description = description + subscription.resource.name + " Subscription "

        # Include the user if this is for an individual that is not the user of this bill
        if subscription.membership.is_individual:
            if subscription.membership.individualmembership.user != self.user:
                description += "(" + subscription.membership.who + ") "

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
    ###########################################################################
    # Coworking Day Methods
    ############################################################################

    def coworking_days(self):
        ''' Return all CoworkingDays associated with this bill. '''
        day_ids = CoworkingDayLineItem.objects.filter(bill=self).values('day')
        return CoworkingDay.objects.filter(id__in=day_ids)

    def includes_coworking_day(self, coworking_day):
        ''' Return True if the given day is in the line items. '''
        return coworking_day in self.coworking_days()

    def add_coworking_day(self, day):
        ''' Add the given coworking day to this bill. '''
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

    @property
    def coworking_day_count(self):
        ''' The number of coworking days associated with this bill. '''
        return self.coworking_days().count()

    @property
    def coworking_day_allowance(self):
        ''' The number of coworking days allowed based on the subscriptions. '''
        return self.resource_allowance(Resource.objects.day_resource)

    @property
    def coworking_day_overage(self):
        ''' The number of coworking days over our allowance. '''
        if self.coworking_day_count < self.coworking_day_allowance:
            return 0
        return self.coworking_day_count - self.coworking_day_allowance

    @property
    def has_coworking_days(self):
        ''' True if there are days or an allowance on this bill. '''
        return self.coworking_day_count > 0 or self.coworking_day_allowance > 0

    ############################################################################
    # Other Methods
    ############################################################################

    def recalculate(self):
        ''' Recalculate bill by evaluating all subscriptions and activity. '''
        logger.info("Recalculating bill %d for %s" % (self.id, self.user))

        # Hold on to the existing data
        subscriptions = list(self.subscriptions())
        coworking_days = list(self.coworking_days().order_by('visit_date'))
        custom_items = list(self.line_items.filter(custom=True))
        total_before = self.amount

        # Delete all the current line items
        for line_item in self.line_items.all():
            if hasattr(line_item, 'day'):
                line_item.day.bill = None
                line_item.day.save()
            line_item.delete()


        # Add everything back
        for s in subscriptions:
            self.add_subscription(s)
        for d in coworking_days:
            self.add_coworking_day(d)
        for c in custom_items:
            c.save()

        logger.debug("Previous amount: %s, New amount: %s" % (total_before, self.amount))

    def combine(self, bill):
        ''' Combine the given bill with this bill. '''
        if bill.user != self.user:
            raise Exception("Can not combine bills from different users (%s and %s)" % (self.user, bill.user))

        # Change the dates
        if bill.period_start < self.period_start:
            self.period_start = bill.period_start
        if bill.period_end > self.period_end:
            self.period_end = bill.period_end
        if bill.due_date > self.due_date:
            self.due_date = bill.due_date
        self.save()

        # Add all the subscriptions, days, and custom items
        for s in bill.subscriptions():
            self.add_subscription(s)
        for d in bill.coworking_days():
            self.add_coworking_day(d)
        for line_item in bill.line_items.filter(custom=True):
            line_item.bill = self
            line_item.save()

        bill.delete()
        self.recalculate()

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
