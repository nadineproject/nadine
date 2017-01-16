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
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from monthdelta import MonthDelta, monthmod

from resource import Resource


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


class MembershipManager2(models.Manager):

    # def create_with_plan(self, user, start_date, end_date, membership_plan, rate=-1, paid_by=None):
    #     if rate < 0:
    #         rate = membership_plan.monthly_rate
    #     self.create(user=user, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
    #                 monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
    #                 has_desk=membership_plan.has_desk, paid_by=paid_by)

    def active_memberships(self, target_date=None):
        if not target_date:
            target_date = timezone.now().date()
        current = Q(allowances__start_date__lte=target_date)
        unending = Q(allowances__end_date__isnull=True)
        future_ending = Q(allowances__end_date__gte=target_date)
        return self.filter(current & (unending | future_ending)).distinct()

    def future_memberships(self):
        today = timezone.now().date()
        return self.filter(allowances__start_date__gte=today)


class Membership2(models.Model):
    objects = MembershipManager2()
    allowances = models.ManyToManyField('ResourceAllowance')


class IndividualMembership(Membership2):
    user = models.ForeignKey(User, related_name="membership")

    def __str__(self):
        return '%s: %s' % (self.user, self.allowances.all())

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
    allowance = models.IntegerField(default=0)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.DecimalField(decimal_places=2, max_digits=9)
    overage_rate = models.DecimalField(decimal_places=2, max_digits=9)
    default = models.ForeignKey(DefaultAllowance)
    bill_day = models.SmallIntegerField(default=0)
    paid_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return "%s: at %s/month" % (self.resource, self.monthly_rate)


class MembershipManager(models.Manager):

    def create_with_plan(self, user, start_date, end_date, membership_plan, rate=-1, paid_by=None):
        if rate < 0:
            rate = membership_plan.monthly_rate
        self.create(user=user, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
                    monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
                    has_desk=membership_plan.has_desk, paid_by=paid_by)

    def active_memberships(self, target_date=None):
        if not target_date:
            target_date = timezone.now().date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.select_related('user', 'user__profile').filter(current & (unending | future_ending)).distinct()

    def future_memberships(self):
        today = timezone.now().date()
        return self.filter(start_date__gte=today)



class Membership(models.Model):

    """A membership level which is billed monthly"""
    objects = MembershipManager()
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
        if Membership.objects.active_memberships(self.start_date).exclude(pk=self.pk).filter(user=self.user).count() != 0:
            raise Exception('Already have a Membership for that start date')
        if self.end_date and Membership.objects.active_memberships(self.end_date).exclude(pk=self.pk).filter(user=self.user).count() != 0:
            raise Exception('Already have a Membership for that end date')
        if self.end_date and self.start_date > self.end_date:
            raise Exception('A Membership cannot start after it ends')
        super(Membership, self).save(*args, **kwargs)

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
        return Membership.objects.filter(user=self.user, end_date=self.start_date - timedelta(days=1)).count() > 0

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
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        ordering = ['start_date']


class SecurityDeposit(models.Model):
    user = models.ForeignKey(User)
    received_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    amount = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=128, blank=True, null=True)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
