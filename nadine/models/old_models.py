from __future__ import unicode_literals

import logging

from datetime import datetime, time, date, timedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.urls import reverse
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings

from nadine.models.membership import Membership

logger = logging.getLogger(__name__)


################################################################################
# Deprecated Models from Pre 2.0
# TODO - remove
################################################################################


class MembershipPlan(models.Model):

    """Options for monthly membership"""
    name = models.CharField(max_length=16)
    description = models.CharField(max_length=128, blank=True, null=True)
    monthly_rate = models.IntegerField(default=0)
    daily_rate = models.IntegerField(default=0)
    dropin_allowance = models.IntegerField(default=0)
    has_desk = models.NullBooleanField(default=False)
    has_key = models.NullBooleanField(default=False)
    has_mail = models.NullBooleanField(default=False)
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
        if not target_date:
            target_date = localtime(now()).date()
        difference = relativedelta(target_date, self.start_date)
        return self.start_date + relativedelta(years=difference.years, months=difference.months)

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


class BillingLog(models.Model):

    """A record of when the billing was last calculated and whether it was successful"""
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(blank=True, null=True)
    successful = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'nadine'
        ordering = ['-started']
        get_latest_by = 'started'

    def __str__(self):
        return 'BillingLog %s: %s' % (self.started, self.successful)

    def ended_date(self):
        if not self.ended:
            return None
        return datetime.date(self.ended)


class OldBill(models.Model):

    """A record of what fees a Member owes."""
    bill_date = models.DateField(blank=False, null=False)
    user = models.ForeignKey(User, related_name="old_bill", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    membership = models.ForeignKey('OldMembership', blank=True, null=True, on_delete=models.CASCADE)
    dropins = models.ManyToManyField('CoworkingDay', related_name='bills')
    guest_dropins = models.ManyToManyField('CoworkingDay', related_name='guest_bills')
    new_member_deposit = models.BooleanField(default=False, blank=False, null=False)
    paid_by = models.ForeignKey(User, blank=True, null=True, related_name='guest_bills', on_delete=models.CASCADE)
    in_progress = models.BooleanField(default=False, blank=False, null=False)

    @property
    def overage_days(self):
        days = self.dropins.count() + self.guest_dropins.count()
        if self.membership and self.membership.dropin_allowance < days:
            return days - self.membership.dropin_allowance
        return 0

    class Meta:
        app_label = 'nadine'
        ordering = ['-bill_date']
        get_latest_by = 'bill_date'

    def __str__(self):
        return 'Old Bill %s [%s]: %s - $%s' % (self.id, self.bill_date, self.user, self.amount)

    def get_admin_url(self):
        return reverse('admin:nadine_bill_change', args=[self.id])


class Transaction(models.Model):

    """A record of charges for a user."""
    transaction_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    TRANSACTION_STATUS_CHOICES = (('open', 'Open'), ('closed', 'Closed'))
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, blank=False, null=False, default='open')
    bills = models.ManyToManyField(OldBill, related_name='transactions')
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'nadine'
        ordering = ['-transaction_date']

    def __str__(self):
        return '%s: %s' % (self.user.get_full_name(), self.amount)

    def get_admin_url(self):
        return reverse('admin:nadine_transaction_change', args=[self.id])
