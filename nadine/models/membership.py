from __future__ import unicode_literals

import os
import uuid
import pprint
import traceback
import operator
import logging
import hashlib
import calendar
from random import random
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from django.db import models
from django.db.models import F, Q, Count, Sum, Value
from django.db.models.functions import Coalesce
from django.contrib import admin
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import Sum
from django.conf import settings
from django.utils.encoding import smart_str
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils.timezone import localtime, now
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.contrib.sites.models import Site

from resource import Resource
from organization import Organization
# from nadine.models import billing

logger = logging.getLogger(__name__)


class MemberGroups():
    ALL = "all"
    HAS_DESK = "has_desk"
    HAS_KEY = "has_key"
    HAS_MAIL = "has_mail"
    NO_MEMBER_AGREEMENT = "no_mem_agmt"
    NO_KEY_AGREEMENT = "no_key_agmt"
    NO_PHOTO = "no_photo"
    STALE_MEMBERSHIP = "stale"

    GROUP_DICT = {
        HAS_DESK: "Members with a Desk",
        HAS_KEY: "Members with Keys",
        HAS_MAIL: "Members with Mail Service",
        NO_MEMBER_AGREEMENT: "Missing Member Agreement",
        NO_KEY_AGREEMENT: "Missing Key Agreement",
        NO_PHOTO: "No Photo",
        STALE_MEMBERSHIP: "Stale Membership",
    }

    @staticmethod
    def get_member_groups():
        group_list = []
        for package in MembershipPackage.objects.filter(enabled=True).order_by('name'):
            if User.helper.members_by_package(package).count() > 0:
                package_name = package.name
                group_list.append((package_name, "%s Members" % package_name))
        for g, d in sorted(MemberGroups.GROUP_DICT.items(), key=operator.itemgetter(0)):
            group_list.append((g, d))
        return group_list

    @staticmethod
    def get_members(group):
        if group == MemberGroups.ALL:
            return User.helper.active_members()
        elif group == MemberGroups.HAS_DESK:
            return User.helper.members_with_desks()
        elif group == MemberGroups.HAS_KEY:
            return User.helper.members_with_keys()
        elif group == MemberGroups.HAS_MAIL:
            return User.helper.members_with_mail()
        elif group == MemberGroups.NO_MEMBER_AGREEMENT:
            return User.helper.missing_member_agreement()
        elif group == MemberGroups.NO_KEY_AGREEMENT:
            return User.helper.missing_key_agreement()
        elif group == MemberGroups.NO_PHOTO:
            return User.helper.missing_photo()
        elif group == MemberGroups.STALE_MEMBERSHIP:
            return User.helper.stale_members()
        else:
            return None


class MembershipPackage(models.Model):
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)

    def monthly_rate(self):
        rate = SubscriptionDefault.objects.filter(package=self).aggregate(Sum('monthly_rate'))['monthly_rate__sum']
        if not rate:
            rate = 0
        return rate

    def __str__(self):
        return self.name


class SubscriptionDefault(models.Model):
    package = models.ForeignKey(MembershipPackage, related_name="defaults", on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, null=True, on_delete=models.CASCADE)
    allowance = models.IntegerField(default=0)
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    overage_rate = models.DecimalField(decimal_places=2, max_digits=9)

    def __str__(self):
        sfx = ""
        if self.allowance > 1:
            sfx = "s"
        return "%d %s%s at %s/month" % (self.allowance, self.resource, sfx, self.monthly_rate)


class MembershipManager(models.Manager):

    def active_memberships(self, target_date=None, package_name=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(subscriptions__start_date__lte=target_date)
        unending = Q(subscriptions__end_date__isnull=True)
        future_ending = Q(subscriptions__end_date__gte=target_date)
        membership_query = self.filter(current & (unending | future_ending)).distinct()
        if package_name:
            membership_query = membership_query.filter(package__name=package_name)
        return membership_query

    def active_individual_memberships(self, target_date=None, package_name=None):
        return self.active_memberships(target_date, package_name).filter(individualmembership__isnull=False)

    def active_organization_memberships(self, target_date=None, package_name=None):
        return self.active_memberships(target_date, package_name).filter(organizationmembership__isnull=False)

    def ready_for_billing(self, target_date=None):
        ''' Return a set of memberships ready for billing.  This
        includes all active memberships that fall on this billing day,
        and the memberships that ended yesterday. '''
        if not target_date:
            target_date = localtime(now()).date()
        ready = []
        memberships_today = self.active_memberships(target_date)
        for m in memberships_today:
            (this_period_start, this_period_end) = m.get_period(target_date)
            if this_period_start == target_date:
                ready.append(m)
        memberships_yesterday = Membership.objects.active_memberships(target_date - timedelta(days=1))
        for m in memberships_yesterday.exclude(id__in=memberships_today.values('id')):
            ready.append(m)
        return ready

    def future_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(subscriptions__start_date__gt=target_date)

    def for_user(self, username, target_date=None):
        # user = User.objects.get(username=username)
        individual = Q(individualmembership__user__username = username)
        organization  = Q(organizationmembership__organization__organizationmember__user__username = username)
        return self.filter(individual or organization)


class Membership(models.Model):
    objects = MembershipManager()
    bill_day = models.SmallIntegerField(default=1)
    package = models.ForeignKey(MembershipPackage, null=True, blank=True, on_delete=models.CASCADE)
    # subscriptions = FK on ResourceSubscription

    @property
    def who(self):
        if self.is_individual:
            return self.individualmembership.user.get_full_name()
        elif self.is_organization:
            return self.organizationmembership.organization.name

    @property
    def who_url(self):
        if self.is_individual:
            return self.individualmembership.user.profile.get_staff_url()
        elif self.is_organization:
            return self.organizationmembership.organization.get_staff_url()

    @property
    def active_now(self):
        return self.is_active()

    @property
    def is_individual(self):
        return hasattr(self, 'individualmembership')

    @property
    def is_organization(self):
        return hasattr(self, 'organizationmembership')

    @property
    def bill_day_str(self):
        # From http://stackoverflow.com/questions/739241/date-ordinal-output
        if 4 <= self.bill_day <= 20 or 24 <= self.bill_day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][self.bill_day % 10 - 1]
        return "%d%s" % (self.bill_day, suffix)

    @property
    def start_date(self):
        first_subscription = self.subscriptions.all().order_by('start_date').first()
        if not first_subscription:
            return None
        return first_subscription.start_date

    def user_list(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.users_in_period(target_date, target_date)

    def users_in_period(self, period_start, period_end):
        if self.is_individual:
            return [self.individualmembership.user]
        elif self.is_organization:
            return list(self.organizationmembership.organization.members_in_period(period_start, period_end))

    def end_all(self, target_date=None):
        '''End all the active subscriptions.  Defaults to yesterday.'''
        if not target_date:
            target_date = localtime(now()).date() - timedelta(days=1)
        for s in self.active_subscriptions():
            s.end_date = target_date
            s.save()

    def end_at_period_end(self):
        ps, pe = self.get_period()
        self.end_all(pe)

    def set_to_package(self, package, start_date=None, end_date=None, paid_by=None):
        if not start_date:
            start_date = localtime(now()).date()

        if self.is_active(start_date):
            raise Exception("Trying to set an active membership to new package!  End the current membership before changing to new package.")

        # Save the package
        self.package = package
        self.save()

        # Add subscriptions for each of the defaults
        for default in package.defaults.all():
            ResourceSubscription.objects.create(
                membership = self,
                start_date = start_date,
                end_date = end_date,
                paid_by = paid_by,
                resource = default.resource,
                monthly_rate = default.monthly_rate,
                overage_rate = default.overage_rate,
                allowance = default.allowance,
            )

    def matches_package(self, target_date=None):
        ''' Calculates if the subscriptions match the package. '''
        if not self.package:
            return False

        # First check the count of subscripitions with the default
        subscriptions = self.active_subscriptions(target_date)
        if self.package.defaults.count() != subscriptions.count():
            return False

        # For every subscription, there should be one default that matches
        for s in subscriptions:
            matches = SubscriptionDefault.objects.filter(package = self.package, resource = s.resource, allowance = s.allowance, monthly_rate = s.monthly_rate, overage_rate = s.overage_rate)
            if matches.count() != 1:
                return False

        # If we've made it this far, it's a match
        return True

    def matching_package(self, subs, target_date=None):
        ''' Calculates which package matches the subscriptions. '''
        subscriptions = self.active_subscriptions(target_date)

        # Loop through all the subscriptions and compile a list of possible matches
        possible_matches = list(MembershipPackage.objects.filter(enabled=True))
        for s in subscriptions:
            matches = SubscriptionDefault.objects.filter(resource = s.resource, allowance = s.allowance, monthly_rate = s.monthly_rate, overage_rate = s.overage_rate).values_list('package', flat=True)
            possible_matches = [p for p in possible_matches if p.id in matches]

        # For all possible matches, check the number of subscriptions against the defaults
        possible_matches = [p for p in possible_matches if p.defaults.count() == subscriptions.count()]

        # If there is only one, we have a match
        if len(possible_matches) == 1:
            return possible_matches[0]

    def active_subscriptions(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.subscriptions.filter(current & (unending | future_ending)).distinct()

    def subscriptions_by_payer(self, target_date=None):
        ''' Pull the active subscriptions for given target_date and group them by payer '''
        subscriptions = {}
        for s in self.active_subscriptions(target_date):
            key = s.payer.username
            if not hasattr(subscriptions, key):
                subscriptions[key] = []
            subscriptions[key].append(s)
        return subscriptions

    def bills_by_payer(self, period_start, period_end):
        ''' Pull the existing bills for a given period and group them by payer '''
        bills = {}
        from billing import UserBill
        for b in UserBill.objects.filter(membership=self, period_start__lte=period_start, period_end__gte=period_end):
            if hasattr(bills, b.user.username):
                raise Exception('Error: multiple bills for one user/date')
            bills[b.user.username] = b
        return bills

    def is_active(self, target_date=None):
        return self.active_subscriptions(target_date).count() > 0

    def in_future(self, target_date=None):
        return self in Membership.objects.future_memberships(target_date)

    def monthly_rate(self, target_date=None):
        rate = self.active_subscriptions(target_date).aggregate(Sum('monthly_rate'))['monthly_rate__sum']
        if not rate:
            rate = 0
        return rate

    def bills_for_period(self, target_date=None):
        ''' Return all bills due for this membership on a given date '''
        ps, pe = self.get_period(target_date)
        return self.bills.filter(due_date=ps)

    def bill_totals(self, target_date=None):
        ''' Return the sum of all bills due for this membership on a given date '''
        total = 0
        for b in self.bills_for_period(target_date):
            total += b.amount
        return total

    def payment_totals(self, target_date=None):
        ''' Return the sum of all bills due for this membership on a given date '''
        total = 0
        for b in self.bills_for_period(target_date):
            total += b.total_paid
        return total

    def get_period(self, target_date=None):
        ''' Get period associated with a certain date.
        Returns (None, None) if the membership is not active.'''
        if not target_date:
            target_date = localtime(now()).date()
        # print("target_date=%s" % target_date)

        # Return None if they were not active on this date
        if not self.is_active(target_date):
            return (None, None)

        # The period starts on the bill_day of the month we're operating in.
        if target_date.day == self.bill_day:
            period_start = target_date
        else:
            month = target_date.month
            year = target_date.year
            if target_date.day < self.bill_day:
                # Go back one month
                month = target_date.month - 1
                if month == 0:
                    # In January go back one year too
                    month = 12
                    year = target_date.year - 1

                # Make sure we are creating a valid date with these
                month_start, month_end = calendar.monthrange(year, month)
                if month_end < self.bill_day:
                    # We went too far, but now we know what to do
                    period_start = date(year, target_date.month, 1)
                    period_end = date(year, target_date.month, self.bill_day - 1)
                    return (period_start, period_end)

            # print("year=%d, month=%s, day=%s" % (year, month, day))
            period_start = date(year, month, self.bill_day)

        period_end = period_start + relativedelta(months=1)
        if period_end.day == period_start.day:
            period_end = period_end - timedelta(days=1)

        return (period_start, period_end)

    def is_period_boundary(self, target_date=None):
        # TODO: Evaluate
        period = self.get_period(target_date=target_date)
        return period and period[1] == target_date

    def next_period_start(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()

        next_period_start = None
        if self.is_active(target_date):
            this_period_start, this_period_end = self.get_period(target_date=target_date)
            next_period_start = this_period_end + timedelta(days=1)
            if not self.is_active(next_period_start):
                next_period_start = None
        else:
            # If this starts in the future then the next period starts then
            future_subscriptions = self.subscriptions.filter(start_date__gt=target_date)
            for s in future_subscriptions:
                if not next_period_start or s.start_date < next_period_start:
                    next_period_start = s.start_date

        return next_period_start

    def last_change(self):
        last_subscription = self.subscriptions.all().order_by('created_ts').last()
        return last_subscription.created_ts

    def generate_bill(self, target_date=None, created_by=None):
        if not target_date:
            target_date = localtime(now()).date()

        # Calculate the period this bill covers
        period_start, period_end = self.get_period(target_date)
        if not period_start:
            return None
        logger.debug('in generate_bill for target_date = %s and get_period = (%s, %s)' % (target_date, period_start, period_end))

        # This method builds up a dictionary called new_bills
        # by looping through the membership/subscription data 4 times.
        # The key is the user who will pay the bill, the value is another dict
        # new_bills = {
        #     'payer1': {
        #         'bill': UserBill
        #         'subscriptions': [ ResourceSubscriptions ]
        #         'line_items': [ BillLineItems() ]
        #         'custom_items': [ BillLineItems(custom=True) ]
        #     }
        #     'payer2': {}
        # }
        new_bills = {}

        # LOOP 1 = Pull the active subscriptions
        for payer, subscriptions in self.subscriptions_by_payer(target_date).items():
            new_bills[payer] = {'subscriptions': subscriptions}

        # LOOP 2 = Check for existing bills & payments
        # Pull the existing bills and check for payments
        # Note: At this point no changes have been made in case of Exceptions
        existing_bills = self.bills_by_payer(period_start, period_end)
        for payer, bill in existing_bills.items():
            logger.debug('Found existing bill #%d for payer %s and period start %s' % (bill.id, bill.user, period_start.strftime("%B %d %Y")))
            if bill.total_paid > 0:
                raise Exception("Attempting to generate new bill when payments are already applied!")
            new_bills[payer]['bill'] = bill

        # LOOP 3 = Clean or create UserBills
        # All clear so we can loop again and clean the existing bills
        # or create new bills if there weren't any existing ones
        for payer, new_bill in new_bills.items():
            if 'bill' in new_bill:
                bill = new_bill['bill']

                # if the bill already exists but the end date is different, it's because we need to prorate
                if bill.period_end != period_end:
                    bill.period_end = period_end
                    bill.save()

                # Save any custom line items before clearing out the old items
                new_bill['custom_items'] = list(bill.line_items.filter(custom=True))

                # Clean out all the existing line items
                for item in bill.line_items.all():
                    item.delete()
            else:
                # Create a new UserBill object
                logger.debug("Generating new bill for %s" % payer)
                user = User.objects.get(username=payer)
                from billing import UserBill
                bill = UserBill.objects.create(
                    user = user,
                    membership = self,
                    due_date = period_start,
                    period_start = period_start,
                    period_end = period_end,
                    created_by = created_by,
                )
                new_bill['bill'] = bill

        # LOOP 4 = Generate Line Items
        for new_bill in new_bills.values():
            bill = new_bill['bill']
            monthly_items = []
            activity_items = []
            for s in new_bill['subscriptions']:
                monthly_items.append(s.monthly_line_item(bill))
                if s.resource.is_trackable():
                    activity_lines = s.activity_line_items(bill)
                    if activity_lines:
                        activity_items.extend(activity_lines)

            # Add them all up (in this specific order)
            new_bill['line_items'] = monthly_items
            new_bill['line_items'].extend(activity_items)
            if 'custom_items' in new_bill:
                new_bill['line_items'].extend(new_bill['custom_items'])

        # LOOP 5 = Save this beautiful bill
        for new_bill in new_bills.values():
            bill = new_bill['bill']
            bill.save()
            for item in new_bill['line_items']:
                if item:
                    # TODO - evaluate why we would get None here --JLS
                    item.save()

        # We've worked so hard to build up this pretty little dictionary
        # we might as well return it!
        return new_bills

    def delete_unpaid_bills(self):
        for bill in self.bills.all():
            if bill.total_paid == 0:
                bill.delete()

    def has_unpaid_bills(self):
        for bill in self.bills.all():
            if not bill.is_paid:
                return True
        return False

    def generate_all_bills(self):
        today = localtime(now()).date()
        period_start = self.start_date
        while period_start and period_start < today:
            self.generate_bill(target_date=period_start)
            period_start = self.next_period_start(period_start)

    # Brought over from modernomad but not ported yet
    # def total_periods(self, target_date=None):
    #     ''' returns total periods between subscription start date and target
    #     date.'''
    #     if not target_date:
    #         target_date = localtime(now()).date()
    #
    #     if self.start_date > target_date:
    #         return 0
    #     if self.end_date and self.end_date < target_date:
    #         target_date = self.end_date
    #
    #     rd = relativedelta(target_date + timedelta(days=1), self.start_date)
    #     return rd.months + (12 * rd.years)
    #
    # def bills_between(self, start, end):
    #     d = start
    #     bills = []
    #     while d < end:
    #         b = self.get_bill_for_date(d)
    #         if b:
    #             bills.append(b)
    #         d = self.next_period_start(d)
    #         if not d:
    #             break
    #     return bills
    #
    # def days_between(self, start, end):
    #     ''' return the number of days of this subscription that occur between start and end dates'''
    #     days = 0
    #     if not self.end_date:
    #         # set the end date to be the end date passed in so we can work with
    #         # a date object, but do NOT save.
    #         self.end_date = end
    #     if self.start_date >= start and self.end_date <= end:
    #         days = (self.end_date - self.start_date).days
    #     elif self.start_date <= start and self.end_date >= end:
    #         days = (end - start).days
    #     elif self.start_date < start:
    #         days = (self.end_date - start).days
    #     elif self.end_date > end:
    #         days = (end - self.start_date).days
    #     return days
    #
    # def last_paid(self, include_partial=False):
    #     ''' returns the end date of the last period with payments, unless no
    #     bills have been paid in which case it returns the start date of the
    #     first period.
    #
    #     If include_partial=True we will count partially paid bills as "paid"
    #     '''
    #     bills = self.bills.order_by('period_start').reverse()
    #     # go backwards in time through the bills
    #     if not bills:
    #         return None
    #     for b in bills:
    #         try:
    #             (paid_until_start, paid_until_end) = self.get_period(target_date=b.period_end)
    #         except:
    #             print "didn't like date"
    #             print b.period_end
    #         if b.is_paid() or (include_partial and b.total_paid() > 0):
    #             return paid_until_end
    #     return b.period_start
    #
    # def update_for_end_date(self, new_end_date):
    #     ''' deletes and regenerates bills after a change in end date'''
    #     self.end_date = new_end_date
    #     self.save()
    #
    #     # if the new end date is not on a period boundary, the final bill needs
    #     # to be pro-rated, so we need to regenerate it.
    #     today = localtime(now()).date()
    #     period_start, period_end = self.get_period(today)
    #
    #     # delete unpaid bills will skip any bills with payments on them.
    #     self.delete_unpaid_bills()
    #
    #     # in general there are SO MANY edge cases about when to regenerate
    #     # bills, that we just regenerate them in all cases.
    #     self.generate_all_bills()
    #
    # def expected_num_bills(self):
    #     today = localtime(now()).date()
    #     period_start = self.start_date
    #     num_expected = 0
    #     while period_start and (period_start < today) and (period_start < self.end_date):
    #         num_expected += 1
    #         period_start = self.next_period_start(period_start)
    #     return num_expected


class IndividualMembership(Membership):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="membership", on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.user, self.subscriptions.all())

    class Meta:
        manager_inheritance_from_future = True


class OrganizationMembership(Membership):
    organization = models.OneToOneField(Organization, related_name="membership", on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (self.organization, self.subscriptions.all())

    class Meta:
        manager_inheritance_from_future = True


class SubscriptionManager(models.Manager):

    def active_subscriptions(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.filter(current & (unending | future_ending)).distinct()

    def active_subscriptions_with_username(self, target_date=None):
        ''' Return the set of active subscriptions including the username for each subscription. '''
        individual_user = F('membership__individualmembership__user__username')
        organization_user = F('membership__organizationmembership__organization__organizationmember__user__username')
        return self.active_subscriptions(target_date).annotate(username=Coalesce(individual_user, organization_user))

    def future_subscriptions(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(start_date__gt=target_date)

    def past_subscriptions(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(end_date__lt=target_date)


class ResourceSubscription(models.Model):
    objects = SubscriptionManager()

    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    membership = models.ForeignKey(Membership, related_name="subscriptions", on_delete=models.CASCADE)
    description = models.CharField(max_length=64, blank=True, null=True)
    allowance = models.IntegerField(default=0)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    overage_rate = models.DecimalField(decimal_places=2, max_digits=9)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        sfx = ""
        if self.allowance > 1:
            sfx = "s"
        desc = ""
        if self.description:
            desc = "(%s)" % self.description
        return "%d %s%s %s at $%s/month" % (self.allowance, self.resource, sfx, desc, self.monthly_rate)

    @property
    def payer(self):
        if self.paid_by:
            return self.paid_by
        if hasattr(self.membership, 'individualmembership'):
            return self.membership.individualmembership.user
        if hasattr(self.membership, 'organizationmembership'):
            return self.membership.organizationmembership.organization.lead
        return None

    def is_active(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.start_date and self.start_date <= target_date and (self.end_date is None or self.end_date >= target_date)

    def prorate_for_period(self, period_start, period_end):
        prorate_start = period_start
        prorate_end = period_end

        if self.end_date and self.end_date < period_end:
            prorate_end = self.end_date
        if self.start_date > period_start:
            prorate_start = self.start_date

        period_days = (period_end - period_start).days
        prorate_days = (prorate_end - prorate_start).days

        return Decimal(prorate_days) / period_days

    def monthly_line_item(self, bill):
        from billing import BillLineItem
        desc = "Monthly " + self.resource.name + " "
        if self.description:
            desc += self.description + " "
        desc += "(%s to %s)" % (bill.period_start, bill.period_end)
        logger.debug("description: %s" % desc)
        prorate = self.prorate_for_period(bill.period_start, bill.period_end)
        logger.debug("prorate = %f" % prorate)
        amount = prorate * self.monthly_rate
        line_item = BillLineItem(bill=bill, description=desc, amount=amount)
        return line_item

    def activity_line_items(self, bill):
        # Get the start and end of the period just before our bill period
        period_start, period_end = self.membership.get_period(bill.period_start - timedelta(days=1))

        # Pull the users active in this period
        user_list = self.membership.users_in_period(period_start, period_end)
        multiple_users = len(user_list) > 1

        tracker = self.resource.get_tracker()

        line_items = []
        allowance_left = self.allowance
        for user in user_list:
            amount = 0
            activity = tracker.get_activity(user, period_start, period_end)
            overage = activity.count() - allowance_left
            if overage > 0:
                amount = overage * self.overage_rate
            allowance_left = allowance_left - activity.count()
            if allowance_left < 0:
                allowance_left = 0

            description = "%ss (%d)" % (self.resource.name, activity.count())
            if multiple_users:
                description = user.get_full_name() + " - " + description

            line_item = tracker.get_line_item(bill, description, amount, activity)
            line_items.append(line_item)

        if len(line_items) > 0:
            return line_items


class SecurityDeposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    received_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    amount = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=128, blank=True, null=True)


################################################################################
# Deprecated Models TODO - remove
################################################################################


class MembershipPlan(models.Model):

    """Options for monthly membership"""
    name = models.CharField(max_length=16)
    description = models.CharField(max_length=128, blank=True, null=True)
    monthly_rate = models.IntegerField(default=0)
    daily_rate = models.IntegerField(default=0)
    dropin_allowance = models.IntegerField(default=0)
    has_desk = models.NullBooleanField(default=False)
    enabled = models.BooleanField(default=True)

    def __str__(self): return self.name

    def get_admin_url(self):
        return reverse('admin:nadine_membershipplan_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "Membership Plan"
        verbose_name_plural = "Membership Plans"


class OldMembershipManager(models.Manager):

    def create_with_plan(self, user, start_date, end_date, membership_plan, rate=-1, paid_by=None):
        if rate < 0:
            rate = membership_plan.monthly_rate
        self.create(user=user, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
                    monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
                    has_desk=membership_plan.has_desk, paid_by=paid_by)

    def active_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.select_related('user', 'user__profile').filter(current & (unending | future_ending)).distinct()

    def future_memberships(self):
        today = localtime(now()).date()
        return self.filter(start_date__gte=today)


class OldMembership(models.Model):

    """A membership level which is billed monthly"""
    objects = OldMembershipManager()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.CASCADE)
    membership_plan = models.ForeignKey(MembershipPlan, null=True, on_delete=models.CASCADE)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.IntegerField(default=0)
    dropin_allowance = models.IntegerField(default=0)
    daily_rate = models.IntegerField(default=0)
    has_desk = models.BooleanField(default=False)
    has_key = models.BooleanField(default=False)
    has_mail = models.BooleanField(default=False)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="guest_membership", on_delete=models.CASCADE)
    new_membership = models.ForeignKey(Membership, null=True, blank=True, on_delete=models.CASCADE)

    @property
    def guest_of(self):
        if self.paid_by:
            return self.paid_by.profile
        return None

    def save(self, *args, **kwargs):
        if OldMembership.objects.active_memberships(self.start_date).exclude(pk=self.pk).filter(user=self.user).count() != 0:
            raise Exception('Already have a Membership for that start date')
        if self.end_date and OldMembership.objects.active_memberships(self.end_date).exclude(pk=self.pk).filter(user=self.user).count() != 0:
            raise Exception('Already have a Membership for that end date')
        if self.end_date and self.start_date > self.end_date:
            raise Exception('A Membership cannot start after it ends')
        super(OldMembership, self).save(*args, **kwargs)

    def is_active(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        if self.start_date > target_date:
            return False
        return self.end_date == None or self.end_date >= target_date

    def is_anniversary_day(self, target_date):
        # Do something smarter if we're at the end of February
        if target_date.month == 2 and target_date.day == 28:
            if self.start_date.day >= 29:
                return True

        # 30 days has September, April, June, and November
        if self.start_date.day == 31 and target_date.day == 30:
            if target_date.month in [9, 4, 6, 11]:
                return True
        return target_date.day == self.start_date.day

    def is_change(self):
        # If there is a membership ending the day before this one began then this one is a change
        return OldMembership.objects.filter(user=self.user, end_date=self.start_date - timedelta(days=1)).count() > 0

    def prev_billing_date(self, target_date=None):
        from monthdelta import monthmod
        if not target_date:
            target_date = localtime(now()).date()
        day_difference = monthmod(self.start_date, target_date)[1]
        return target_date - day_difference

    def next_billing_date(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.prev_billing_date(target_date) + relativedelta(months=1)

    def get_allowance(self):
        if self.paid_by:
            m = self.paid_by.profile.active_membership()
            if m:
                return m.dropin_allowance
            else:
                return 0
        return self.dropin_allowance

    def __str__(self):
        return '%s - %s - %s' % (self.start_date, self.user, self.membership_plan)

    def get_admin_url(self):
        return reverse('admin:nadine_membership_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "OldMembership"
        verbose_name_plural = "OldMemberships"
        ordering = ['start_date']


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
