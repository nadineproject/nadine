import logging
import traceback
from decimal import Decimal
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import F, Q, Count, Sum, Value, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.db.models.fields import DecimalField
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.functional import cached_property

from nadine.models.membership import Membership, ResourceSubscription
from nadine.models.resource import Resource
from nadine.models.usage import CoworkingDay, Event

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

    def __str__(self):
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
                target_date = localtime(last_batch.created_ts).date()

            # Run for each day in our range
            while target_date <= end_date:
                self.run_billing_for_day(target_date)
                target_date = target_date + timedelta(days=1)

            # Close out batch
            self.close()

            # Update cached totals on all associated bills
            for bill in self.bills.all():
                bill.update_cached_totals()

        except Exception as e:
            # Save all error messages
            self.error = str(e)
            traceback.print_exc()
            logger.error(self.error)
            self.close()

        # Indicate if we ran successsfully or not
        return self.successful

    def run_billing_for_day(self, target_date):
        ''' Run billing for a specific day. '''
        logger.info("run_billing_for_day(%s)" % target_date)

        # Gather up all the subscriptions
        self.run_subscriptions(target_date)

        # Gather up all the trackable usage (CoworkingDays and Events)
        self.run_usage(target_date)

        # Recalculate all the bills that need it
        for bill in self.to_recalculate:
            bill.recalculate()

        # Close all open subscription based bills that end on this day
        self.close_bills_at_end_of_period(target_date)

    def run_subscriptions(self, target_date):
        # Keep track of which bills need to be recalculated
        self.to_recalculate = set()

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
                line_item = bill.add_subscription(subscription)
                self.bills.add(bill)
                # If we have any activity for this resource, flag for recalculation
                activity = bill.resource_activity(subscription.resource)
                if activity and activity.count() > 0:
                    self.to_recalculate.add(bill)

    def run_usage(self, target_date):
        # Pull and add all past unbilled CoworkingDays
        for day in CoworkingDay.objects.unbilled(target_date).order_by('visit_date'):
            logger.debug("Found Coworking Day: %s %s %s" % (day.user, day.visit_date, day.payment))
            # Find the open bill for the period of this one day
            bill = UserBill.objects.get_or_create_open_bill(day.payer, day.visit_date, day.visit_date)
            bill.add_coworking_day(day)
            self.bills.add(bill)

        # Pull and add all past unbilled Events
        for event in Event.objects.unbilled(target_date).order_by('start_ts'):
            day = event.start_ts.date()
            logger.debug("Found Event: %s %s" % (event.user, day))
            # Find the open bill for the period of this one day
            bill = UserBill.objects.get_or_create_open_bill(event.payer, day, day)
            bill.add_event(event)

    def close_bills_at_end_of_period(self, target_date):
        ''' Close the open bills at the end of their period. '''
        logger.debug("close_bills_at_end_of_period(target_date=%s)" % target_date)
        for bill in UserBill.objects.filter(closed_ts__isnull=True, period_end=target_date):
            if bill.subscriptions().count() > 0:
                # Only close bills that have subscriptions.
                # Bills with only resource activity remain open until paid
                bill.close()
                self.bills.add(bill)

    def close(self):
        self.completed_ts = localtime(now())
        self.save()


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
            raise Exception("Found more than one bill (%s)!" % bills)

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

    # def outstanding(self):
    #     ''' Return a set of all outstanding bills. '''
    #     # There is a known bug that results in a bill that has multiple line items
    #     # and a partial payment not showing up in this set as it should.
    #     # https://code.djangoproject.com/ticket/10060
    #     # https://github.com/nadineproject/nadine/issues/300
    #     amount_adjustment = (F('bill_amount') * F('items_distinct')) / F('item_count')
    #     tax_amount_adjustment = (F('bill_tax_amount') * F('items_distinct')) / F('item_count')
    #     payment_adjustment = (F('payment_amount') * F('payments_distinct')) / F('payment_count')
    #     outstanding_query = self.filter(mark_paid=False) \
    #         .annotate(bill_amount=Sum('line_items__amount', output_field=DecimalField())) \
    #         .annotate(bill_tax_amount=Sum('line_items__tax_amount', output_field=DecimalField())) \
    #         .annotate(item_count=Count('line_items')) \
    #         .annotate(items_distinct=Count('line_items', distinct=True)) \
    #         .annotate(payment_amount=Sum('payment__amount', output_field=DecimalField())) \
    #         .annotate(payment_count=Count('payment')) \
    #         .annotate(payments_distinct=Count('payment', distinct=True)) \
    #         .annotate(adjusted_amount=ExpressionWrapper(amount_adjustment, output_field=DecimalField())) \
    #         .annotate(adjusted_tax_amount=ExpressionWrapper(tax_amount_adjustment, output_field=DecimalField())) \
    #         .annotate(adjusted_payments=ExpressionWrapper(payment_adjustment, output_field=DecimalField())) \
    #         .annotate(owed=F('adjusted_amount') + F('adjusted_tax_amount') - F('adjusted_payments'))
    #         # .annotate(total=F('bill_amount') + F('bill_tax_amount')) \
    #     no_payments = Q(payments_distinct = 0)
    #     partial_payment = Q(owed__gt = 0)
    #     return outstanding_query.filter(bill_amount__gt=0).filter(no_payments | partial_payment)

    def outstanding(self):
        return self.filter(mark_paid=False, cached_total_owed__gt = 0) \
            .annotate(bill_total=F('cached_total_amount') + F('cached_total_tax_amount'))

    def non_zero(self):
        return self \
            .annotate(bill_amount=Sum('line_items__amount')) \
            .annotate(bill_tax_amount=Sum('line_items__tax_amount')) \
            .filter(bill_amount__gt=0)

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

    cached_total_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    cached_total_tax_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    cached_total_paid = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    cached_total_owed = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    def __str__(self):
        return "UserBill %d: %s %s to %s for $%s" % (self.id, self.user, self.period_start, self.period_end, self.total) # self.amount)

    ############################################################################
    # Basic Properties
    ############################################################################

    @property
    def total_paid(self):
        return self.payment_set.aggregate(paid=Coalesce(Sum('amount'), Value(0.00)))['paid']

    @property
    def total_owed(self):
        return self.total - self.total_paid

    @property
    def amount(self):
        return self.line_items.aggregate(amount=Coalesce(Sum('amount'), Value(0.00)))['amount']

    @property
    def tax_amount(self):
        return self.total_tax_applied()

    @property
    def total(self):
        return self.amount + self.tax_amount

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
    def subscriptions_due(self):
        ''' True if this bill is not paid and the amount paid is less than the montnly rate. '''
        if self.is_paid:
            return False
        if not self.monthly_rate:
            return False
        return self.total_paid < self.monthly_rate

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
        if resource == Resource.objects.event_resource:
            return self.events()

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
        description_start = self.period_start
        if subscription.start_date > self.period_start:
            description_start = subscription.start_date
        description_end = self.period_end
        if subscription.end_date and subscription.end_date < self.period_end:
            description_end = subscription.end_date
        if description_start != self.period_start or description_end != self.period_end:
            description += "(%s to %s)" % (description_start, description_end)

        # Calculate our amount
        prorate = subscription.prorate_for_period(self.period_start, self.period_end)
        amount = prorate * subscription.monthly_rate

        # Create our new line item
        line_item = SubscriptionLineItem.objects.create(
            bill = self,
            subscription = subscription,
            description = description,
            amount = amount
        )
        self.add_lineitem_taxes(line_item.calculate_taxes())
        return line_item

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
            billable_count = self.coworking_day_billable_count + 1
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
        self.add_lineitem_taxes(line_item.calculate_taxes())
        return line_item


    @property
    def coworking_day_count(self):
        ''' The number of coworking days on with this bill. '''
        return self.coworking_days().count()

    @property
    def coworking_day_billable_count(self):
        ''' The number of billable coworking days on this bill. '''
        return self.coworking_days().filter(payment="Bill").count()

    @property
    def coworking_day_allowance(self):
        ''' The number of coworking days allowed based on the subscriptions. '''
        return self.resource_allowance(Resource.objects.day_resource)

    @property
    def coworking_day_overage(self):
        ''' The number of billable coworking days over our allowance. '''
        if self.coworking_day_billable_count < self.coworking_day_allowance:
            return 0
        return self.coworking_day_billable_count - self.coworking_day_allowance

    ###########################################################################
    # Event Methods
    ############################################################################

    def events(self):
        ''' Return all Events associated with this bill. '''
        event_ids = EventLineItem.objects.filter(bill=self).values('event')
        return Event.objects.filter(id__in=event_ids)

    def includes_event(self, event):
        ''' Return True if the given event is in the line items. '''
        return event in self.events()

    def calculate_event_charge(self, event):
        # First check to see if there is a set charge on this event
        if event.charge:
            return event.charge
        else:
            if not event.room:
                raise Exception("Event must have room specified or a specific charge set.")

        if self.user.membership.active_subscriptions():
            total_hours = self.event_hours_used + event.hours
            overage = total_hours - self.event_hour_allowance
            if overage < 0:
                overage = 0.00

        # Member only rooms get charged depending on subscriptions
        if event.room.members_only:
            return overage * float(self.event_hour_overage_rate)

        # Calculate the charge based on the default rate for the room
        if self.event_hour_allowance == 0:
            return event.room.default_rate
        else:
            # If there is an allowance, they are an active member and get a discount
            return float(event.room.default_rate) * getattr(settings, "MEMBER_DISCOUNT_EVENTS", 1.0) * overage

    def calculate_event_description(self, event):
        day = str(event.start_ts.date())
        if event.description:
            return "Event on %s: %s" % (day, event.description)

        description = "Booking on %s for %s hours" % (day, event.hours)
        # Append the username if it's different from this bill
        if event.user != self.user:
            description += " by " + event.user.username
        return description

    def add_event(self, event):
        ''' Add the given event to this bill. '''
        logger.debug("add_event(%s)" % event)
        amount = self.calculate_event_charge(event)
        description = self.calculate_event_description(event)
        line_item = EventLineItem.objects.create(
            bill = self,
            description = description,
            amount = amount,
            event = event,
        )
        self.add_lineitem_taxes(line_item.calculate_taxes())
        return line_item

    @property
    def event_count(self):
        ''' The number of events on this bill. '''
        return self.events().count()

    @property
    def event_hours_used(self):
        ''' The number of event hours on this bill. '''
        hours = 0
        for event in self.events():
            hours += event.hours
        return hours

    @property
    def event_hour_allowance(self):
        ''' The number of event hours allowed based on the subscriptions. '''
        return self.resource_allowance(Resource.objects.event_resource)

    @property
    def event_hour_overage_rate(self):
        ''' The rate per hour if over the allowance. '''
        return self.resource_overage_rate(Resource.objects.event_resource)

    @property
    def event_hour_overage(self):
        ''' The number of hours over our allowance. '''
        if self.event_hours < self.event_hour_allowance:
            return 0
        return self.event_hours - self.event_hour_allowance

    ############################################################################
    # Tax Methods
    # TODO: Consider putting these in their own module.
    ############################################################################

    def calculate_taxes(self):
        ''' Calculates applicable taxes based on bill's line items '''
        taxes = []
        for item in SubscriptionLineItem.objects.filter(bill=self):
            taxes += item.calculate_taxes()
        for item in CoworkingDayLineItem.objects.filter(bill=self):
            taxes += item.calculate_taxes()
        for item in EventLineItem.objects.filter(bill=self):
            taxes = item.calculate_taxes()
        return taxes

    def add_lineitem_taxes(self, lineitem_taxes):
        ''' Applies line item taxes to bill (saves them to DB) '''
        for (lineitem_tax) in lineitem_taxes:
            lineitem_tax.save()

    def total_tax_applied(self):
        ''' Provide the total amount of tax added to bill '''
        total = 0
        for _,amount in self.total_tax_applied_by_rate():
            total += amount
        return total

    def total_tax_applied_by_rate(self):
        ''' Produce list of tax rates and amounts (rate<TaxRate>, amount<Decimal>) '''
        taxes = []
        for taxrate in TaxRate.objects.all():
            total = self.total_tax_applied_for_rate(taxrate)
            taxes.append((taxrate, total))
        return taxes

    def total_tax_applied_for_rate(self, rate):
        ''' Total tax amount applied for given rate '''
        total = 0
        for item in BillLineItem.objects.filter(bill=self):
            tax = item.get_applied_tax(rate)
            if tax is not None:
                total += tax.amount
        return total

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

        # Delete all the line items
        for line_item in self.line_items.all():
            line_item.delete()

        # Add everything back
        for s in subscriptions:
            self.add_subscription(s)
        for d in coworking_days:
            self.add_coworking_day(d)
        for c in custom_items:
            c.save()

        # Recalculate the cache as well
        self.update_cached_totals()

        logger.debug("Previous amount: %s, New amount: %s" % (total_before, self.amount))

    def combine(self, bill, recalculate=True):
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

        # Pull all the line items in to memory and delete the other bill
        subscriptions = list(bill.subscriptions())
        coworking_days = list(bill.coworking_days())
        events = list(bill.events())
        custom_items = list(bill.line_items.filter(custom=True))
        bill.delete()

        # Add all the subscriptions, days, and custom items
        for s in subscriptions:
            self.add_subscription(s)
        for d in coworking_days:
            self.add_coworking_day(d)
        for e in events:
            self.add_event(e)
        for line_item in custom_items:
            line_item.bill = self
            line_item.save()

        if recalculate:
            self.recalculate()

    def update_cached_totals(self):
        self.cached_total_amount = self.amount
        self.cached_total_tax_amount = self.tax_amount
        self.cached_total_paid = self.total_paid
        self.cached_total_owed = self.total_owed
        self.save()

    def close(self):
        if self.closed_ts != None:
            raise Exception("Bill is already closed!")
        self.closed_ts = localtime(now())
        self.in_progress = False
        self.save()


class BillLineItem(models.Model):
    bill = models.ForeignKey(UserBill, related_name="line_items", null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    custom = models.BooleanField(default=False)

    @property
    def applicable_taxes(self):
        resource = self.get_resource()
        return resource.taxrate_set.all()

    @cached_property
    def applied_taxes(self):
        return self.lineitemtax_set.all()

    """ Get an instance of tax if rate has been applied """
    def get_applied_tax(self, rate):
        return self.lineitemtax_set.filter(tax_rate=rate.id).first()

    def has_tax_applied(self, rate):
        return self.get_applied_tax(rate) is not None

    def calculate_taxes(self):
        taxes = []
        if self.amount == 0:
            return taxes
        for rate in self.applicable_taxes:
            tax = self.get_applied_tax(rate)
            # Ensure we only calculate tax once.
            if tax is None:
                tax = LineItemTax(
                    line_item=self,
                    tax_rate=rate,
                    amount=self.calculate_tax_amount(rate)
                )
            taxes.append(tax)
        return taxes

    def calculate_tax_amount(self, rate):
        return self.amount * rate.percentage

    def __str__(self):
        return self.description


class SubscriptionLineItem(BillLineItem):
    subscription = models.ForeignKey('ResourceSubscription', related_name="line_items", on_delete=models.CASCADE)

    def get_resource(self):
        return self.subscription.resource


class CoworkingDayLineItem(BillLineItem):
    day = models.OneToOneField('CoworkingDay', related_name="line_item", on_delete=models.CASCADE)

    def get_resource(self):
        return Resource.objects.resource_by_key(Resource.objects.DAY_KEY)


class EventLineItem(BillLineItem):
    event = models.OneToOneField('Event', related_name="line_item", on_delete=models.CASCADE)

    def get_resource(self):
        return Resource.objects.resource_by_key(Resource.objects.EVENT_KEY)


class PaymentMethod(models.Model):
    name = models.CharField(max_length=128, help_text="e.g., Stripe, Visa, cash, bank transfer")

    def __str__(self):
        return self.name


class Payment(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    bill = models.ForeignKey(UserBill, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    external_id = models.CharField(max_length=128, null=True, blank=True, help_text="ID used by payment service")
    note = models.TextField(blank=True, null=True, help_text="Private notes about this payment")

    def __str__(self):
        return "%s: %s - $%s" % (str(self.created_ts)[:16], self.user, self.amount)


class StripeBillingProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    customer_email = models.EmailField(help_text="Customer email address used with Stripe customer record")
    customer_id = models.CharField(max_length=128, help_text="Stripe customer ID used for billing via Stripe")

    def __str__(self):
        return "{} ({}): {}".format(self.user, self.customer_email, self.customer_id)


class TaxRate(models.Model):
    name = models.CharField(max_length=256, help_text="The name of the tax")
    percentage = models.DecimalField(max_digits=3, decimal_places=2, help_text="Tax percentage")
    resources = models.ManyToManyField(Resource)

    def __str__(self):
        return "{} ({}%)".format(self.name, self.percentage * 100)


class LineItemTax(models.Model):
    line_item = models.ForeignKey(BillLineItem, on_delete=models.CASCADE)
    tax_rate = models.ForeignKey(TaxRate, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return "{}, {} for {}".format(self.line_item.bill, self.tax_rate, self.line_item)

    @cached_property
    def calculate_tax_rate(self):
        # Figure out the tax rate from amount and line_item.amount
        pass


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
