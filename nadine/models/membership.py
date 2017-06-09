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

    # Based on entered action, returns those which were started or ended within the given time period
    def date_range(self, start=None, end=None, action=None):
        if not start:
            start = localtime(now()).date()
        if not end:
            end = localtime(now()).date()
        if action == "started":
            query = Q(subscriptions__start_date__gte=start, subscriptions__start_date__lte=end)
        if action == "ended":
            query = Q(subscriptions__end_date__gte=start, subscriptions__end_date__lte=end)
        membership_query = self.filter(query)
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

    @property
    def end_date(self):
        subscriptions = self.subscriptions.all()
        open_subscriptions = self.subscriptions.filter(end_date=None)
        if not subscriptions or open_subscriptions:
            return None
        return subscriptions.order_by('end_date').last().end_date

    def package_name(self, target_date=None):
        ''' Determine the package name from the active ResourceSubscriptions '''
        packaged_subscriptions = self.active_subscriptions(target_date).filter(package_name__isnull=False)
        if packaged_subscriptions:
            return packaged_subscriptions.first().package_name
        return None

    def package_is_pure(self, target_date=None):
        ''' True if we have one and only one package name and no blank package names '''
        package_count = self.active_subscriptions(target_date).values('package_name').count()
        no_package_subscriptions = self.active_subscriptions(target_date).filter(package_name=None).count()
        return package_count == 1 and no_package_subscriptions == 0

    def allowance_by_resource(self, resource, target_date=None):
        return self.active_subscriptions(target_date).filter(resource=resource).aggregate(Sum('allowance'))['allowance__sum']

    def has_resource(self, resource, target_date=None):
        return self.active_subscriptions(target_date).filter(resource=resource).count() > 0

    def has_key(self, target_date=None):
        return self.has_resource(Resource.objects.key_resource, target_date)

    def has_desk(self, target_date=None):
        return self.has_resource(Resource.objects.desk_resource, target_date)

    def has_mail(self, target_date=None):
        return self.has_resource(Resource.objects.mail_resource, target_date)

    def users_in_period(self, period_start, period_end):
        users = set()
        if self.is_individual:
            # The user themselves
            users.add(self.individualmembership.user)
            guest_subscriptions = ResourceSubscription.objects.filter(paid_by=self.individualmembership.user)
            for s in guest_subscriptions:
                users = users.union(s.membership.users_in_period(period_start, period_end))
        elif self.is_organization:
            organization = self.organizationmembership.organization
            members = organization.members_in_period(period_start, period_end)
            users = set(members)
        return users

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

    def set_to_package(self, package, start_date=None, end_date=None, paid_by=None, bill_day=None):
        if not start_date:
            start_date = localtime(now()).date()

        if self.is_active(start_date):
            raise Exception("Trying to set an active membership to new package!  End the current membership before changing to new package.")

        # Save the package
        if bill_day:
            self.bill_day = bill_day
        self.save()

        # Add subscriptions for each of the defaults
        for default in package.defaults.all():
            ResourceSubscription.objects.create(
                membership = self,
                package_name = package.name,
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

        # Pull the package name and the coresponding package
        package_name = self.package_name(target_date)
        if not package_name:
            return False
        package = MembershipPackage.objects.filter(name=package_name).first()
        if not package:
            return False

        # Check the count of subscripitions with the default
        subscriptions = self.active_subscriptions(target_date)
        if package.defaults.count() != subscriptions.count():
            return False

        # For every subscription, there should be one default that matches
        for s in subscriptions:
            matches = SubscriptionDefault.objects.filter(package = package, resource = s.resource, allowance = s.allowance, monthly_rate = s.monthly_rate, overage_rate = s.overage_rate)
            if matches.count() != 1:
                return False

        # If we've made it this far, it's a match
        return True

    def matching_package(self, target_date=None, subscriptions=None):
        ''' Calculates which package matches the subscriptions. '''
        if not subscriptions:
            if not target_date:
                target_date = localtime(now()).date()
            subscriptions = self.active_subscriptions(target_date)
        count = 0

        # Loop through all the subscriptions and compile a list of possible matches
        possible_matches = list(MembershipPackage.objects.filter(enabled=True))
        for s in subscriptions:
            if type(s) is dict:
                 matches = SubscriptionDefault.objects.filter(resource = s['resource'], allowance = s['allowance'], monthly_rate = s['monthly_rate'], overage_rate = s['overage_rate']).values_list('package', flat=True)
            else:
                matches = SubscriptionDefault.objects.filter(resource = s.resource, allowance = s.allowance, monthly_rate = s.monthly_rate, overage_rate = s.overage_rate).values_list('package', flat=True)
            count = count + 1
            possible_matches = [p for p in possible_matches if p.id in matches]

        # For all possible matches, check the number of subscriptions against the defaults
        possible_matches = [p for p in possible_matches if p.defaults.count() == count]

        # If there is only one, we have a match
        if len(possible_matches) == 1:
            return possible_matches[0]

    def active_subscriptions(self, target_date=None):
        ''' Return the active subscriptions on a given day. '''
        if not target_date:
            target_date = localtime(now()).date()
        return self.subscriptions_for_period(period_start=target_date, period_end=target_date)

    def subscriptions_for_period(self, period_start, period_end):
        ''' Return the active subscriptions for a given period. '''
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=period_end)
        return self.subscriptions.filter(start_date__lte=period_start).filter(unending | future_ending).distinct()

    def subscriptions_by_payer(self, target_date=None):
        ''' Pull the active subscriptions for given target_date and group them by payer '''
        subscriptions = {}
        for s in self.active_subscriptions(target_date):
            key = s.payer.username
            if not key in subscriptions:
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
        ''' Return the date of the last subscription change on this membership. '''
        last_subscription = self.subscriptions.all().order_by('created_ts').last()
        return last_subscription.created_ts

    def generate_all_bills(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = localtime(now()).date()
        period_start = start_date
        while period_start and period_start < end_date:
            self.generate_bill(target_date=period_start)
            period_start = self.next_period_start(period_start)

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
        # The key is the user who will pay the bill, the value is another dict.
        # new_bills = {
        #     'payer1': {
        #         'bill': UserBill
        #         'subscriptions': [ ResourceSubscriptions ]
        #         'line_items': [ BillLineItems() ]
        #         'custom_items': [ BillLineItems(custom=True) ]
        #     },
        #     'payer2': {},
        #     ...
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
            # Every subscription produces a monthly line item
            for subscription in new_bill['subscriptions']:
                monthly_items.append(bill.generate_monthly_line_item(subscription))
            for resource in Resource.objects.all():
                if resource.is_trackable():
                    activity_lines = bill.generate_activity_line_items(resource)
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

    def resource_activity(self, resource, target_date=None):
        ps, pe = self.get_period(target_date)
        return self.resource_activity_for_period(resource, ps, pe)

    def resource_activity_for_period(self, resource, period_start, period_end):
        activity_set = set()
        tracker = resource.get_tracker()
        for user in self.users_in_period(period_start, period_end):
            for activity in tracker.get_activity(user, period_start, period_end):
                activity_set.add(activity)
        return activity_set

    def delete_unpaid_bills(self):
        for bill in self.bills.all():
            if bill.total_paid == 0:
                bill.delete()

    def has_unpaid_bills(self):
        for bill in self.bills.all():
            if not bill.is_paid:
                return True
        return False


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

    def all_subscriptions_by_member(self, target_ate=None):
        ''' Return set of subscriptions by member '''
        individual_user = F('membership__individualmembership__user__username')
        return self.all().annotate(username=individual_user)

    def future_subscriptions(self, target_date=None):
        '''Return set of subscriptions with start date in the future '''
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(start_date__gt=target_date)

    def past_subscriptions(self, target_date=None):
        ''' Return set of subscriptions with end date in the past '''
        if not target_date:
            target_date = localtime(now()).date()
        return self.filter(end_date__lt=target_date)


class ResourceSubscription(models.Model):
    objects = SubscriptionManager()

    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", null=True, blank=True, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    membership = models.ForeignKey(Membership, related_name="subscriptions", on_delete=models.CASCADE)
    package_name = models.CharField(max_length=64, blank=True, null=True)
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
    def user(self):
        if hasattr(self.membership, 'individualmembership'):
            return self.membership.individualmembership.user
        if hasattr(self.membership, 'organizationmembership'):
            return self.membership.organizationmembership.organization.lead
        return None

    @property
    def payer(self):
        if self.paid_by:
            return self.paid_by
        return self.user

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


class SecurityDeposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    received_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    amount = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=128, blank=True, null=True)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
