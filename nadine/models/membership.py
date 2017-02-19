from __future__ import unicode_literals

import os
import uuid
import pprint
import traceback
import operator
import logging
import hashlib
from random import random
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.encoding import smart_str
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils.timezone import localtime, now
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from monthdelta import MonthDelta, monthmod

from resource import Resource
from organization import Organization

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
        for plan in MembershipPlan.objects.filter(enabled=True).order_by('name'):
            plan_name = plan.name
            plan_users = User.helper.members_by_plan(plan_name)
            if plan_users.count() > 0:
                group_list.append((plan_name, "%s Members" % plan_name))
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


class MembershipManager(models.Manager):

    # def create_with_plan(self, user, start_date, end_date, membership_plan, rate=-1, paid_by=None):
    #     if rate < 0:
    #         rate = membership_plan.monthly_rate
    #     self.create(user=user, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
    #                 monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
    #                 has_desk=membership_plan.has_desk, paid_by=paid_by)

    def active_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(allowances__start_date__lte=target_date)
        unending = Q(allowances__end_date__isnull=True)
        future_ending = Q(allowances__end_date__gte=target_date)
        return self.filter(current & (unending | future_ending)).distinct()

    def ready_for_billing(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        ready = []
        for m in self.active_memberships():
            (this_period_start, this_period_end) = m.get_period()
            if this_period_start == target_date:
                ready.append(m)
        return ready

    def future_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(allowances__start_date__gt=target_date)

    def active_members(self, target_date=None):
        members = []
        for membership in self.active_memberships(target_date):
            if membership.individualmembership:
                members.append(membership.individualmembership.user)
            elif membership.organizationmembership:
                org = membership.organizationmembership.organization
                members.extend(org.members())
        return members

    def for_user(self, username, target_date=None):
        user = User.objects.get(username=username)
        individual = Q(individualmembership__user = user)
        organization  = Q(organizationmembership__organization__organizationmember__user = user)
        return Membership.objects.filter(individual or organization)


class Membership(models.Model):
    objects = MembershipManager()
    bill_day = models.SmallIntegerField(default=1)
    allowances = models.ManyToManyField('ResourceAllowance')

    def active_allowances(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.allowances.filter().filter(current & (unending | future_ending)).distinct()

    def is_active(self, target_date=None):
        return self.active_allowances(target_date).count() > 0

    def in_future(self, target_date=None):
        return self in Membership.objects.future_memberships(target_date)

    def monthly_rate(self, target_date=None):
        rate = 0
        # This should be done with some form of SUM query --JLS
        for a in self.active_allowances(target_date):
            rate = rate + a.monthly_rate
        return rate

    def get_period(self, target_date=None):
        ''' Get period associated with a certain date.
        Returns (None, None) if the membership is not active.'''
        if not target_date:
            target_date = localtime(now()).date()

        # Return None if they were not active on this date
        if not self.is_active(target_date):
            return (None, None)

        # The period starts on the bill_ay of the month we're operating in.
        if target_date.day == self.bill_day:
            period_start = target_date
        else:
            month = target_date.month
            year = target_date.year
            if target_date.day < self.bill_day:
                if target_date.day == 1:
                    month = 12
                    year = target_date.year - 1
                else:
                    month = target_date.month - 1
            period_start = date(year, month, self.bill_day)

        # The period ends one month later
        period_end = period_start + relativedelta(months=1)
        if period_end.day == period_start.day:
            period_end = period_end - timedelta(days=1)

        return (period_start, period_end)

    def is_period_boundary(self, target_date=None):
        period = self.get_period(target_date=target_date)
        return period and period[1] == target_date

    def get_next_period_start(self, target_date=None):
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
            future_allowances = self.allowances.filter(start_date__gt=target_date)
            for a in future_allowances:
                if not next_period_start or a.start_date < next_period_start:
                    next_period_start = a.start_date

        return next_period_start

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
    #         d = self.get_next_period_start(d)
    #         if not d:
    #             break
    #     return bills
    #
    # def get_bill_for_date(self, date):
    #     result = SubscriptionBill.objects.filter(subscription=self, period_start__lte=date, period_end__gte=date)
    #     logger.debug('subscription %d: get_bill_for_date %s' % (self.id, date))
    #     logger.debug('bill object(s):')
    #     logger.debug(result)
    #     if result.count():
    #         if result.count() > 1:
    #             logger.debug("Warning! Multiple bills found for one date. This shouldn't happen")
    #             raise Exception('Error: multiple bills for one date:')
    #         return result[0]
    #     else:
    #         return None
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

    def generate_bill(self, delete_old_items=True, target_date=None):
        ''' used to generate or regenerate a bill for the given target date, or
        today.  the reason old line items are generally deleted is that we want
        to make sure that a) the line item descriptions are correct, since they
        are simply strings generated from the line items themselves, and b)
        because if any fees have changed, then percentage based derivative fees
        will also change. '''

        if not target_date:
            target_date = localtime(now()).date()

        period_start, period_end = self.get_period(target_date)
        if not period_start:
            return None
        logger.debug(' ')
        logger.debug('in generate_bill for target_date = %s and get_period = (%s, %s)' % (target_date, period_start, period_end))

        # a subscription's last cycle could be a pro rated one. check to see if
        # the subscription end date is before the period end; if so, change the
        # period end to be the subscription end date.
        prorated = False
        if self.end_date and self.end_date < period_end:
            prorated = True
            original_period_end = period_end
            period_end = self.end_date

        try:
            bill = SubscriptionBill.objects.get(period_start=period_start, subscription=self)
            logger.debug('Found existing bill #%d for period start %s' % (bill.id, period_start.strftime("%B %d %Y")))
            # if the bill already exists but we're updating it to be prorated,
            # we need to change the period end also.
            if prorated and bill.period_end != period_end:
                bill.period_end = period_end
                bill.save()
            # If we already have a bill and we don't want to clear out the old data
            # we can stop right here and go with the existing line items.
            if not delete_old_items:
                return list(bill.line_items)
        except Exception, e:
            logger.debug("Generating new bill item")
            bill = SubscriptionBill.objects.create(period_start=period_start, period_end=period_end)

        # Save any custom line items before clearing out the old items
        logger.debug("working with bill %d (%s)" % (bill.id, bill.period_start.strftime("%B %d %Y")))
        custom_items = list(bill.line_items.filter(custom=True))
        if delete_old_items:
            if bill.total_paid() > 0:
                logger.debug("Warning: modifying a bill with payments on it.")
            for item in bill.line_items.all():
                item.delete()

        line_items = []
        # First line item is the subscription itself.
        desc = "%s (%s to %s)" % (self.description, period_start, period_end)
        if prorated:
            period_days = Decimal((period_end - period_start).days)
            original_period_days = (original_period_end - period_start).days
            price = (period_days/original_period_days)*self.price
        else:
            price = self.price

        line_item = BillLineItem(bill=bill, description=desc, amount=price, paid_by_house=False)
        line_items.append(line_item)

        # Incorporate any custom fees or discounts. As well, track the
        # effective resource charge to be used in calculation of percentage-based
        # fees
        effective_bill_charge = price
        for item in custom_items:
            line_items.append(item)
            effective_bill_charge += item.amount  # may be negative
            logger.debug(item.amount)
        logger.debug('effective room charge after discounts: %d' % effective_bill_charge)

        # For now we are going to assume that all fees (of any kind) that are marked as "paid by house"
        # will be applied to subscriptions as well -- JLS
        for location_fee in LocationFee.objects.filter(location=self.location, fee__paid_by_house=True):
            desc = "%s (%s%c)" % (location_fee.fee.description, (location_fee.fee.percentage * 100), '%')
            amount = float(effective_bill_charge) * location_fee.fee.percentage
            logger.debug('Fee %s for %d' % (desc, amount))
            fee_line_item = BillLineItem(bill=bill, description=desc, amount=amount, paid_by_house=True, fee=location_fee.fee)
            line_items.append(fee_line_item)

        # Save this beautiful bill
        bill.save()
        for item in line_items:
            item.save()
        self.bills.add(bill)
        self.save()

        return line_items

    def generate_all_bills(self, target_date=None):
        today = localtime(now()).date()

        if not target_date:
            target_date = self.start_date

        if self.end_date and self.end_date < today:
            end_date = self.end_date
        else:
            end_date = today

        period_start = target_date
        while period_start and (period_start < today) and (period_start < end_date):
            self.generate_bill(target_date=period_start)
            period_start = self.get_next_period_start(period_start)

    # Ported from modernomad
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
    # def delete_unpaid_bills(self):
    #     for bill in self.bills.all():
    #         if bill.total_paid() == 0:
    #             bill.delete()
    #
    # def has_unpaid_bills(self):
    #     for bill in self.bills.all():
    #         if not bill.is_paid():
    #             return True
    #     return False
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
    #         period_start = self.get_next_period_start(period_start)
    #     return num_expected


class IndividualMembership(Membership):
    user = models.OneToOneField(User, related_name="membership")

    def __str__(self):
        return '%s: %s' % (self.user, self.allowances.all())


class OrganizationMembership(Membership):
    organization = models.OneToOneField(Organization, related_name="membership")


class MembershipPackage(models.Model):
    name = models.CharField(max_length=64)
    allowances = models.ManyToManyField('DefaultAllowance')

    def __str__(self): return self.name


class DefaultAllowance(models.Model):
    resource = models.ForeignKey(Resource, null=True)
    allowance = models.IntegerField(default=0)
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    overage_rate = models.DecimalField(decimal_places=2, max_digits=9)

    def __str__(self):
        return "%d %s at %s/month" % (self.allowance, self.resource, self.monthly_rate)


class ResourceAllowance(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="+", null=True)
    resource = models.ForeignKey(Resource, null=True)
    description = models.TextField(blank=True, null=True)
    allowance = models.IntegerField(default=0)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    overage_rate = models.DecimalField(decimal_places=2, max_digits=9)
    default = models.ForeignKey(DefaultAllowance, null=True, blank=True)
    paid_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return "%s: at %s/month" % (self.resource, self.monthly_rate)

    def is_active(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.start_date <= target_date and (self.end_date is None or self.end_date >= target_date)


class SecurityDeposit(models.Model):
    user = models.ForeignKey(User)
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
        return urlresolvers.reverse('admin:nadine_membershipplan_change', args=[self.id])

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
    user = models.ForeignKey(User, related_name="+")
    membership_plan = models.ForeignKey(MembershipPlan, null=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.IntegerField(default=0)
    dropin_allowance = models.IntegerField(default=0)
    daily_rate = models.IntegerField(default=0)
    has_desk = models.BooleanField(default=False)
    has_key = models.BooleanField(default=False)
    has_mail = models.BooleanField(default=False)
    paid_by = models.ForeignKey(User, null=True, blank=True, related_name="guest_membership")

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

    def is_active(self, on_date=None):
        if not on_date:
            on_date = date.today()
        if self.start_date > on_date:
            return False
        return self.end_date == None or self.end_date >= on_date

    def is_anniversary_day(self, test_date):
        # Do something smarter if we're at the end of February
        if test_date.month == 2 and test_date.day == 28:
            if self.start_date.day >= 29:
                return True

        # 30 days has September, April, June, and November
        if self.start_date.day == 31 and test_date.day == 30:
            if test_date.month in [9, 4, 6, 11]:
                return True
        return test_date.day == self.start_date.day

    def is_change(self):
        # If there is a membership ending the day before this one began then this one is a change
        return OldMembership.objects.filter(user=self.user, end_date=self.start_date - timedelta(days=1)).count() > 0

    def prev_billing_date(self, test_date=None):
        if not test_date:
            test_date = date.today()
        day_difference = monthmod(self.start_date, test_date)[1]
        return test_date - day_difference

    def next_billing_date(self, test_date=None):
        if not test_date:
            test_date = date.today()
        return self.prev_billing_date(test_date) + MonthDelta(1)

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
        return urlresolvers.reverse('admin:nadine_membership_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "OldMembership"
        verbose_name_plural = "OldMemberships"
        ordering = ['start_date']


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
