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
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

# imports for signals
import django.dispatch
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from PIL import Image

from nadine.utils.payment_api import PaymentAPI
from nadine.utils.slack_api import SlackAPI
from nadine.models.usage import CoworkingDay
from nadine.models.payment import Bill
from nadine import email

from doors.keymaster.models import DoorEvent

logger = logging.getLogger(__name__)


GENDER_CHOICES = (
    ('U', 'Unknown'),
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)


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


class HowHeard(models.Model):

    """A record of how a person discovered the space"""
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class Industry(models.Model):

    """The type of work a user does"""
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        ordering = ['name']


class Neighborhood(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class UserQueryHelper():

    def active_members(self):
        active_members = Q(id__in=Membership.objects.active_memberships().values('user'))
        return User.objects.select_related('profile').filter(active_members).order_by('first_name')

    def here_today(self, day=None):
        if not day:
            day = timezone.now().date()

        # The members who are on the network
        from arpwatch.arp import users_for_day_query
        arp_members_query = users_for_day_query(day=day)

        # The members who have signed in
        daily_members_query = User.objects.filter(id__in=CoworkingDay.objects.filter(visit_date=day).values('user__id'))

        # The members that have access a door
        door_query = DoorEvent.objects.users_for_day(day)
        door_members_query = User.helper.active_members().filter(id__in=door_query.values('user'))

        combined_query = arp_members_query | daily_members_query | door_members_query
        return combined_query.distinct()

    def not_signed_in(self, day=None):
        if not day:
            day = timezone.now().date()

        signed_in = []
        for l in CoworkingDay.objects.filter(visit_date=day):
            signed_in.append(l.user)

        not_signed_in = []
        for u in self.here_today(day):
            if not u in signed_in and not u.profile.has_desk(day):
                not_signed_in.append({'user':u, 'day':day})

        return not_signed_in

    def not_signed_in_since(self, day=None):
        if not day:
            day = timezone.now().date()
        not_signed_in = []

        d = timezone.now().date()
        while day <= d:
            not_signed_in.extend(self.not_signed_in(d))
            d = d - timedelta(days=1)

        return not_signed_in

    def exiting_members(self, day=None):
        if day == None:
            day = timezone.now()
        next_day = day + timedelta(days=1)

        # Exiting members are here today and gone tomorrow.  Pull up all the active
        # memberships for today and remove the list of active members tomorrow.
        today_memberships = Membership.objects.active_memberships(day)
        tomorrow_memberships = Membership.objects.active_memberships(next_day)
        exiting = today_memberships.exclude(user__in=tomorrow_memberships.values('user'))

        return User.objects.filter(id__in=exiting.values('user'))

    def active_member_emails(self):
        emails = []
        for membership in Membership.objects.active_memberships():
            for e in EmailAddress.objects.filter(user=membership.user):
                if e.email not in emails:
                    emails.append(e.email)
        return emails

    def expired_slack_users(self):
        expired_users = []
        active_emails = self.active_member_emails()
        slack_users = SlackAPI().users.list()
        for u in slack_users.body['members']:
            if 'profile' in u and 'real_name' in u and 'email' in u['profile']:
                email = u['profile']['email']
                if email and email not in active_emails and 'nadine' not in email:
                    expired_users.append({'email':email, 'real_name':u['real_name']})
        return expired_users

    def stale_member_date(self):
        three_months_ago = timezone.now() - MonthDelta(3)
        return three_months_ago

    def stale_members(self):
        smd = self.stale_member_date()
        recently_used = CoworkingDay.objects.filter(visit_date__gte=smd).values('user').distinct()
        memberships = Membership.objects.active_memberships().filter(start_date__lte=smd, has_desk=False)
        return User.objects.filter(id__in=memberships.values('user')).exclude(id__in=recently_used).order_by('first_name')

    def missing_member_agreement(self):
        active_agmts = FileUpload.objects.filter(document_type=FileUpload.MEMBER_AGMT, user__in=self.active_members()).distinct()
        users_with_agmts = active_agmts.values('user')
        return self.active_members().exclude(id__in=users_with_agmts).order_by('first_name')

    def missing_key_agreement(self):
        active_agmts = FileUpload.objects.filter(document_type=FileUpload.KEY_AGMT, user__in=self.active_members()).distinct()
        users_with_agmts = active_agmts.values('user')
        return self.members_with_keys().exclude(id__in=users_with_agmts).order_by('first_name')

    def missing_photo(self):
        return self.active_members().filter(profile__photo="").order_by('first_name')

    def invalid_billing(self):
        active_memberships = Membership.objects.active_memberships()
        free_memberships = active_memberships.filter(monthly_rate=0)
        freeloaders = Q(id__in=free_memberships.values('user'))
        guest_memberships = active_memberships.filter(paid_by__isnull=False)
        guests = Q(id__in=guest_memberships.values('user'))
        active_invalids = self.active_members().filter(profile__valid_billing=False)
        return active_invalids.exclude(freeloaders).exclude(guests)

    def members_by_plan(self, plan):
        memberships = Membership.objects.active_memberships().filter(membership_plan__name=plan)
        return User.objects.filter(id__in=memberships.values('user')).order_by('first_name')

    def members_with_desks(self):
        memberships = Membership.objects.active_memberships().filter(has_desk=True)
        return User.objects.filter(id__in=memberships.values('user')).order_by('first_name')

    def members_with_keys(self):
        memberships = Membership.objects.active_memberships().filter(has_key=True)
        return User.objects.filter(id__in=memberships.values('user')).order_by('first_name')

    def members_with_mail(self):
        memberships = Membership.objects.active_memberships().filter(has_mail=True)
        return User.objects.filter(id__in=memberships.values('user')).order_by('first_name')

    def members_by_neighborhood(self, hood, active_only=True):
        if active_only:
            return self.active_members().filter(profile__neighborhood=hood)
        else:
            return User.objects.filter(profile__neighborhood=hood)

    def members_with_tag(self, tag):
        return self.active_members().filter(profile__tags__name__in=[tag])

    def managers(self, include_future=False):
        if hasattr(settings, 'TEAM_MEMBERSHIP_PLAN'):
            management_plan = MembershipPlan.objects.filter(name=settings.TEAM_MEMBERSHIP_PLAN).first()
            memberships = Membership.objects.active_memberships().filter(membership_plan=management_plan).distinct()
            if include_future:
                memberships = memberships | Membership.objects.future_memberships().filter(membership_plan=management_plan).distinct()
            return User.objects.filter(id__in=memberships.values('user'))
        return None

    def search(self, search_string, active_only=False):
        terms = search_string.split()
        if len(terms) == 0:
            return None

        if active_only:
            user_query = self.active_members()
        else:
            user_query = User.objects.all()

        if '@' in terms[0]:
            return user_query.filter(id__in=EmailAddress.objects.filter(email=terms[0]).values('user'))
        else:
            fname_query = Q(first_name__icontains=terms[0])
            lname_query = Q(last_name__icontains=terms[0])
            for term in terms[1:]:
                fname_query = fname_query | Q(first_name__icontains=term)
                lname_query = lname_query | Q(last_name__icontains=term)
            user_query = user_query.filter(fname_query | lname_query)

        return user_query.order_by('first_name')

    def by_email(self, email):
        email_address = EmailAddress.objects.filter(email=email).first()
        if email_address:
            return email_address.user
        return None

User.helper = UserQueryHelper()


def user_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return "user_photos/%s.%s" % (instance.user.username, ext.lower())


class UserProfile(models.Model):
    MAX_PHOTO_SIZE = 1024

    user = models.OneToOneField(User, blank=False, related_name="profile")
    phone = PhoneNumberField(blank=True, null=True)
    phone2 = PhoneNumberField("Alternate Phone", blank=True, null=True)
    address1 = models.CharField(max_length=128, blank=True)
    address2 = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zipcode = models.CharField(max_length=16, blank=True)
    bio = models.TextField(blank=True, null=True)
    public_profile = models.BooleanField(default=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="U")
    howHeard = models.ForeignKey(HowHeard, blank=True, null=True)
    #referred_by = models.ForeignKey(User, verbose_name="Referred By", related_name="referral", blank=True, null=True)
    industry = models.ForeignKey(Industry, blank=True, null=True)
    neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True)
    has_kids = models.NullBooleanField(blank=True, null=True)
    self_employed = models.NullBooleanField(blank=True, null=True)
    company_name = models.CharField(max_length=128, blank=True, null=True)
    last_modified = models.DateField(auto_now=True, editable=False)
    photo = models.ImageField(upload_to=user_photo_path, blank=True, null=True)
    tags = TaggableManager(blank=True)
    valid_billing = models.NullBooleanField(blank=True, null=True)

    def url_personal(self):
        return self.user.url_set.filter(url_type__name="personal").first()

    def url_professional(self):
        return self.user.url_set.filter(url_type__name="professional").first()

    def url_facebook(self):
        return self.user.url_set.filter(url_type__name="facebook").first()

    def url_twitter(self):
        return self.user.url_set.filter(url_type__name="twitter").first()

    def url_linkedin(self):
        return self.user.url_set.filter(url_type__name="linkedin").first()

    def url_github(self):
        return self.user.url_set.filter(url_type__name="github").first()

    def save_url(self, url_type, url_value):
        if url_type and url_value:
            url = self.user.url_set.filter(url_type__name=url_type).first()
            if url:
                url.url_value = url_value
                url.save()
            else:
                t = URLType.objects.get(name=url_type)
                URL.objects.create(user=self.user, url_type=t, url_value=url_value)

    def all_bills(self):
        """Returns all of the open bills, both for this user and any bills for other members which are marked to be paid by this member."""
        return Bill.objects.filter(models.Q(user=self.user) | models.Q(paid_by=self.user)).order_by('-bill_date')

    def open_bills(self):
        """Returns all of the open bills, both for this user and any bills for other members which are marked to be paid by this member."""
        return Bill.objects.filter(models.Q(user=self.user) | models.Q(paid_by=self.user)).filter(transactions=None).order_by('bill_date')

    def open_bill_amount(self):
        total = 0
        for b in self.open_bills():
            total = total + b.amount
        return total

    def open_bills_amount(self):
        """Returns the amount of all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
        return Bill.objects.filter(models.Q(user=self.user) | models.Q(paid_by=self.user)).filter(transactions=None).aggregate(models.Sum('amount'))['amount__sum']

    def open_xero_invoices(self):
        from nadine.utils.xero_api import XeroAPI
        xero_api = XeroAPI()
        return xero_api.get_open_invoices(self.user)

    def pay_bills_form(self):
        from staff.forms import PayBillsForm
        return PayBillsForm(initial={'username': self.user.username, 'amount': self.open_bills_amount})

    def last_bill(self):
        """Returns the latest Bill, or None if the member has not been billed.
        NOTE: This does not (and should not) return bills which are for other members but which are to be paid by this member."""
        bills = Bill.objects.filter(user=self.user)
        if len(bills) == 0:
            return None
        return bills[0]

    def membership_history(self):
        return Membership.objects.filter(user=self.user).order_by('-start_date', 'end_date')

    def membership_on_date(self, day):
        return Membership.objects.filter(user=self.user, start_date__lte=day).filter(Q(end_date__isnull=True) | Q(end_date__gte=day)).first()

    def last_membership(self):
        """Returns the latest membership, even if it has an end date, or None if none exists"""
        memberships = Membership.objects.filter(user=self.user).order_by('-start_date', 'end_date')[0:]
        if memberships == None or len(memberships) == 0:
            return None
        return memberships[0]

    def active_membership(self):
        for membership in self.membership_history():
            if membership.is_active():
                return membership
        return None

    def membership_for_day(self, day):
        return Membership.objects.active_memberships(target_date=day).filter(user=self.user).first()

    def activity_this_month(self, test_date=None):
        if not test_date:
            test_date = date.today()

        membership = self.active_membership()
        if membership:
            if membership.paid_by:
                # Return host's activity
                host = membership.paid_by
                return host.profile.activity_this_month()
            month_start = membership.prev_billing_date(test_date)
        else:
            # Just go back one month from this date since there isn't a membership to work with
            month_start = test_date - MonthDelta(1)

        activity = []
        for h in [self.user] + self.guests():
            for l in CoworkingDay.objects.filter(user=h, payment='Bill', visit_date__gte=month_start):
                activity.append(l)
        for l in CoworkingDay.objects.filter(paid_by=self.user, payment='Bill', visit_date__gte=month_start):
            activity.append(l)
        return activity

    def activity(self):
        return CoworkingDay.objects.filter(user=self.user)

    def paid_count(self):
        return self.activity().filter(payment='Bill').count()

    def first_visit(self):
        if Membership.objects.filter(user=self.user).count() > 0:
            return Membership.objects.filter(user=self.user).order_by('start_date')[0].start_date
        else:
            if CoworkingDay.objects.filter(user=self.user).count() > 0:
                return CoworkingDay.objects.filter(user=self.user).order_by('visit_date')[0].visit_date
            else:
                return None

    def all_emails(self):
        # Done in two queries so that the primary email address is always on top.
        primary = self.user.emailaddress_set.filter(is_primary=True)
        non_primary = self.user.emailaddress_set.filter(is_primary=False)
        return list(primary) + list(non_primary)

    def non_primary_emails(self):
        return self.user.emailaddress_set.filter(is_primary=False)

    def duration(self):
        return relativedelta(timezone.now().date(), self.first_visit())

    def duration_str(self, include_days=False):
        retval = ""
        delta = self.duration()
        if delta.years:
            if delta.years == 1:
                retval = "1 year"
            else:
                retval = "%d years" % delta.years
            if delta.months or delta.days:
                retval += " and "
        if delta.months:
            if delta.months == 1:
                retval += "1 month"
            else:
                retval += "%d months" % delta.months
            if include_days and delta.days:
                retval += " and "
        if include_days and delta.days:
            if delta.days == 1:
                retval += "1 day"
            else:
                retval += "%d days" % delta.days
        return retval

    def hosted_days(self):
        return CoworkingDay.objects.filter(paid_by=self.user).order_by('-visit_date')

    def has_file_uploads(self):
        return FileUpload.objects.filter(user=self.user).count() > 0

    def has_file(self, doc_type):
        return FileUpload.objects.filter(user=self.user, document_type=doc_type).count() > 0

    def file_uploads(self):
        files = {}
        # Only want the latest one if there are duplicates
        for f in FileUpload.objects.filter(user=self.user).order_by('uploadTS').reverse():
            files[f.name] = f
        return files.values()

    def files_by_type(self):
        files = {}
        # Only want the latest one if there are duplicates
        for f in FileUpload.objects.filter(user=self.user).order_by('uploadTS').reverse():
            files[f.document_type] = f
        return files

    def alerts_by_key(self, include_resolved=False):
        from nadine.models.alerts import MemberAlert
        if include_resolved:
            alerts = MemberAlert.objects.filter(user=self.user)
        else:
            alerts = MemberAlert.objects.filter(user=self.user, resolved_ts__isnull=True, muted_ts__isnull=True)
        alerts_by_key = {}
        for alert in alerts:
            if alert.key in alerts_by_key:
                alerts_by_key[alert.key].append(alert)
            else:
                alerts_by_key[alert.key] = [alert]
        return alerts_by_key

    def alerts(self):
        from nadine.models.alerts import MemberAlert
        return MemberAlert.objects.filter(user=self.user).order_by('-created_ts')

    def open_alerts(self):
        from nadine.models.alerts import MemberAlert
        return MemberAlert.objects.filter(user=self.user, resolved_ts__isnull=True, muted_ts__isnull=True).order_by('-created_ts')

    def resolve_alerts(self, alert_key, resolved_by=None):
        logger.debug("resolve_alerts: user=%s, key=%s, resolved_by=%s" % (self.user, alert_key, resolved_by))
        from nadine.models.alerts import MemberAlert
        alerts = MemberAlert.objects.filter(user=self.user, key=alert_key, resolved_ts__isnull=True, muted_ts__isnull=True).order_by('-created_ts')
        if alerts:
            for alert in alerts:
                alert.resolve(resolved_by)

    def member_since(self):
        first = self.first_visit()
        if first == None:
            return None
        return timezone.localtime(timezone.now()) - datetime.combine(first, time(0, 0, 0))

    def last_visit(self):
        if CoworkingDay.objects.filter(user=self.user).count() > 0:
            return CoworkingDay.objects.filter(user=self.user).latest('visit_date').visit_date
        else:
            if Membership.objects.filter(user=self.user, end_date__isnull=False).count() > 0:
                return Membership.objects.filter(user=self.user, end_date__isnull=False).latest('end_date').end_date
            else:
                return None

    def membership_type(self):
        active_membership = self.active_membership()
        if active_membership:
            return active_membership.membership_plan
        else:
            last_monthly = self.last_membership()
            if last_monthly:
                return "Ex" + str(last_monthly.membership_plan)

        # Now check daily logs
        drop_ins = CoworkingDay.objects.filter(user=self.user).count()
        if drop_ins == 0:
            return "New User"
        elif drop_ins == 1:
            return "First Day"
        else:
            return "Drop-in"

    def is_active(self):
        m = self.active_membership()
        return m is not None

    def has_desk(self, target_date=None):
        if not target_date:
            target_date = timezone.now().date()
        m = self.membership_on_date(target_date)
        return m and m.has_desk

    def is_guest(self):
        m = self.active_membership()
        if m and m.is_active() and m.paid_by:
            return m.paid_by
        return None

    def guests(self):
        guests = []
        for membership in Membership.objects.filter(paid_by=self.user):
            if membership.is_active():
                guests.append(membership.user)
        return guests

    def has_valid_billing(self):
        host = self.is_guest()
        if host and host != self.user:
            return host.profile.has_valid_billing()
        if self.valid_billing is None:
            logger.debug("%s: Null Valid Billing" % self)
            if self.has_new_card():
                logger.debug("%s: Found new card.  Marking billing valid." % self)
                self.valid_billing = True
                self.save()
            else:
                self.valid_billing = False
        return self.valid_billing

    def has_billing_profile(self):
        try:
            api = PaymentAPI()
            if api.get_customers(self.user.username):
                return True
        except Exception:
            pass
        return False

    def has_new_card(self):
        # Check for a new card.  WARNING: kinda expensive
        try:
            api = PaymentAPI
            return api.has_new_card(self.user.username)
        except Exception:
            pass
        return False

    # TODO - Remove
    def deposits(self):
        return SecurityDeposit.objects.filter(user=self.user)

    def __str__(self): return '%s %s' % (smart_str(self.user.first_name), smart_str(self.user.last_name))

    def auto_bill_enabled(self):
        api = PaymentAPI()
        return api.auto_bill_enabled(self.user.username)

    # TODO - Remove
    def member_notes(self):
        return MemberNote.objects.filter(user=self.user)

    # TODO - Remove
    def special_days(self):
        return SpecialDay.objects.filter(user=self.user)

    def membership_days(self):
        total_days = 0
        for membership in self.membership_history():
            end = membership.end_date
            if not end:
                end = timezone.now().date()
            diff = end - membership.start_date
            days = diff.days
            total_days = total_days + days
        return total_days

    def average_bill(self):
        from nadine.models.payment import Bill
        bills = Bill.objects.filter(user=self.user)
        if bills:
            bill_totals = 0
            for b in bills:
                bill_totals = bill_totals + b.amount
            return bill_totals / len(bills)
        return 0

    def is_manager(self):
        if hasattr(settings, 'TEAM_MEMBERSHIP_PLAN'):
            management_plan = MembershipPlan.objects.filter(name=settings.TEAM_MEMBERSHIP_PLAN).first()
            if management_plan:
                active_membership = self.active_membership()
                if active_membership:
                    return active_membership.membership_plan == management_plan
        return False

    class Meta:
        app_label = 'nadine'
        ordering = ['user__first_name', 'user__last_name']
        get_latest_by = "last_modified"

def profile_save_callback(sender, **kwargs):
    profile = kwargs['instance']
    # Process the member alerts
    from nadine.models.alerts import MemberAlert
    MemberAlert.objects.trigger_profile_save(profile)
post_save.connect(profile_save_callback, sender=UserProfile)

def user_save_callback(sender, **kwargs):
    user = kwargs['instance']
    # Make certain we have a Member record
    if not UserProfile.objects.filter(user=user).count() > 0:
        UserProfile.objects.create(user=user)
post_save.connect(user_save_callback, sender=User)

# Add some handy methods to Django's User object
#User.get_profile = lambda self: Member.objects.get_or_create(user=self)[0]
#User.profile = property(User.get_profile)

@receiver(post_save, sender=UserProfile)
def size_images(sender, instance, **kwargs):
    if instance.photo:
        image = Image.open(instance.photo)
        old_x, old_y = image.size
        if old_x > UserProfile.MAX_PHOTO_SIZE or old_y > UserProfile.MAX_PHOTO_SIZE:
            print("Resizing photo for %s" % instance.user.username)
            if old_y > old_x:
                new_y = UserProfile.MAX_PHOTO_SIZE
                new_x = int((float(new_y) / old_y) * old_x)
            else:
                new_x = UserProfile.MAX_PHOTO_SIZE
                new_y = int((float(new_x) / old_x) * old_y)
            new_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            new_image.save(instance.photo.path, image.format)
        image.close()


class EmailAddress(models.Model):
    """An e-mail address for a Django User. Users may have more than one
    e-mail address. The address that is on the user object itself as the
    email property is considered to be the primary address, for which there
    should also be an EmailAddress object associated with the user.

    Pulled from https://github.com/scott2b/django-multimail
    """
    user = models.ForeignKey(User)
    email = models.EmailField(max_length=100, unique=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    verif_key = models.CharField(max_length=40)
    verified_ts = models.DateTimeField(default=None, null=True, blank=True)
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    remote_host = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    def __unicode__(self):
        return self.email

    def is_verified(self):
        """Is this e-mail address verified? Verification is indicated by
        existence of a verified timestamp which is the time the user
        followed the e-mail verification link."""
        return bool(self.verified_ts)

    def set_primary(self):
        """Set this e-mail address to the primary address by setting the
        email property on the user."""
        # If we are already primary, we're done
        if self.is_primary:
            return

        # Make sure the user has the same email address
        if self.user.email != self.email:
            self.user.email = self.email
            self.user.save()

        # Now go through and unset all other email addresses
        for email in self.user.emailaddress_set.all():
            if email == self:
                email.is_primary = True
                email.save(verify=False)
            else:
                if email.is_primary:
                    email.is_primary = False
                    email.save(verify=False)

    def generate_verif_key(self):
        salt = hashlib.sha1(str(random())).hexdigest()[:5]
        self.verif_key = hashlib.sha1(salt + self.email).hexdigest()
        self.save()

    def get_verif_key(self):
        if not self.verif_key:
            self.generate_verif_key()
        return self.verif_key

    def get_verify_link(self):
        verify_link = settings.EMAIL_VERIFICATION_URL
        if not verify_link:
            site = Site.objects.get_current()
            verif_key = self.get_verif_key()
            uri = reverse('email_verify', kwargs={'email_pk': self.id}) + "?verif_key=" + verif_key
            verify_link = "http://" + site.domain + uri
        return verify_link

    def get_send_verif_link(self):
        return reverse('email_verify', kwargs={'email_pk': self.id}) + "?send_link=True"

    def get_set_primary_link(self):
        return reverse('email_manage', kwargs={'email_pk': self.id, 'action':'set_primary'})

    def get_delete_link(self):
        return reverse('email_manage', kwargs={'email_pk': self.id, 'action':'delete'})

    def save(self, verify=True, *args, **kwargs):
        """Save this EmailAddress object."""
        if not self.verif_key:
            self.generate_verif_key()
        if verify and not self.pk:
            # Skip verification if this is an update
            verify = True
        else:
            verify = False
        super(EmailAddress, self).save(*args, **kwargs)
        if verify:
            email.send_verification(self)

    def delete(self):
        """Delete this EmailAddress object."""
        if self.is_primary:
            next_email = self.user.emailaddress_set.exclude(email=self.email).first()
            if not next_email:
                raise Exception("Can not delete last email address!")
            next_email.set_primary()
        super(EmailAddress, self).delete()

def sync_primary_callback(sender, **kwargs):
    user = kwargs['instance']
    try:
        email_address = EmailAddress.objects.get(email=user.email)
    except ObjectDoesNotExist:
        email_address = EmailAddress(user=user, email=user.email)
        email_address.save(verify=False)
    email_address.set_primary()
post_save.connect(sync_primary_callback, sender=User)


class URLType(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class URL(models.Model):
    user = models.ForeignKey(User)
    url_type = models.ForeignKey(URLType)
    url_value = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.url_value

    class Meta:
        app_label = 'nadine'


class EmergencyContact(models.Model):
    user = models.OneToOneField(User, blank=False)
    name = models.CharField(max_length=254, blank=True)
    relationship = models.CharField(max_length=254, blank=True)
    phone = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s - %s' % (self.user.username, self.name)

def emergency_callback_save_callback(sender, **kwargs):
    contact = kwargs['instance']
    contact.last_updated = timezone.now()
pre_save.connect(emergency_callback_save_callback, sender=EmergencyContact)

# Create a handy method on User to get an EmergencyContact
User.get_emergency_contact = lambda self: EmergencyContact.objects.get_or_create(user=self)[0]


class XeroContact(models.Model):
    user = models.OneToOneField(User, related_name="xero_contact")
    xero_id = models.CharField(max_length=64)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return '%s - %s' % (self.user.username, self.xero_id)


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
    user = models.ForeignKey(User)
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

    objects = MembershipManager()

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


class SentEmailLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True)
    recipient = models.EmailField()
    subject = models.CharField(max_length=128, blank=True, null=True)
    success = models.NullBooleanField(blank=False, null=False, default=False)
    note = models.TextField(blank=True, null=True)

    def __str__(self): return '%s: %s' % (self.created, self.recipient)


class SecurityDeposit(models.Model):
    user = models.ForeignKey(User)
    received_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    amount = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=128, blank=True, null=True)


class SpecialDay(models.Model):
    user = models.ForeignKey(User)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    day = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.CharField(max_length=128, blank=True, null=True)


class MemberNote(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, related_name='+')
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s - %s: %s' % (self.created.date(), self.user.username, self.note)


class FileUploadManager(models.Manager):

    def pdf_from_string(self, file_user, file_data, document_type, uploaded_by):
        pdf_file = ContentFile(file_data)
        file_name = document_type + ".pdf"
        upload_obj = FileUpload(user=file_user, name=file_name, document_type=document_type, content_type="application/pdf", uploaded_by=uploaded_by)
        upload_obj.file.save(file_name, pdf_file)
        upload_obj.save()
        return upload_obj

    def create_from_file(self, file_user, file_obj, document_type, uploaded_by):
        file_name = self.file_name_from_document_type(file_obj.name, document_type)
        upload_obj = FileUpload(user=file_user, file=file_obj, name=file_name, document_type=document_type, content_type=file_obj.content_type, uploaded_by=uploaded_by)
        upload_obj.save()
        return upload_obj

    def file_name_from_document_type(self, filename, document_type):
        if document_type and document_type != "None":
            ext = filename.split('.')[-1]
            if ext:
                filename = "%s.%s" % (document_type, ext.lower())
            else:
                filename = document_type
        return filename


def user_file_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    if ext:
        filename = "file_uploads/%s/%s.%s" % (instance.user.username, uuid.uuid4(), ext)
    else:
        filename = "file_uploads/%s/%s" % (instance.user.username, uuid.uuid4())
    return filename


class FileUpload(models.Model):
    MEMBER_INFO = "Member_Information"
    MEMBER_AGMT = "Member_Agreement"
    KEY_AGMT = "Key_Agreement"
    EVENT_AGMT = "Event_Host_Agreement"

    DOC_TYPES = (
        (MEMBER_INFO, 'Member Information'),
        (MEMBER_AGMT, 'Membership Agreement'),
        (KEY_AGMT, 'Key Holder Agreement'),
        (EVENT_AGMT, 'Event Host Agreement'),
    )

    uploadTS = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, blank=False)
    name = models.CharField(max_length=64)
    content_type = models.CharField(max_length=64)
    file = models.FileField(upload_to=user_file_upload_path, blank=False)
    document_type = models.CharField(max_length=200, choices=DOC_TYPES, default=None, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, related_name="uploaded_by")

    def is_pdf(self):
        if not self.content_type:
            return False
        return self.content_type == "application/pdf"

    def is_image(self):
        if not self.content_type:
            return False
        return self.content_type.startswith("image")

    def is_text(self):
        if not self.content_type:
            return False
        return self.content_type.startswith("text")

    def __unicode__(self):
        return '%s - %s: %s' % (self.uploadTS.date(), self.user, self.name)

    objects = FileUploadManager()


def file_upload_callback(sender, **kwargs):
    file_upload = kwargs['instance']
    from nadine.models.alerts import MemberAlert
    MemberAlert.objects.trigger_file_upload(file_upload.user)
post_save.connect(file_upload_callback, sender=FileUpload)


# Not ready yet.  This was pulled in from modernomads. --JLS
# Keys need to be updated to keys in nadine.email.py

# class EmailTemplate(models.Model):
#     ''' Template overrides for system generated emails '''
#
#     ADMIN_DAILY = 'admin_daily_update'
#     GUEST_DAILY = 'guest_daily_update'
#     INVOICE = 'invoice'
#     RECEIPT = 'receipt'
#     SUBSCRIPTION_RECEIPT = 'subscription_receipt'
#     NEW_RESERVATION = 'newreservation'
#     WELCOME = 'pre_arrival_welcome'
#     DEPARTURE = 'departure'
#
#     KEYS = (
#     (ADMIN_DAILY, 'Admin Daily Update'),
#     (GUEST_DAILY, 'Guest Daily Update'),
#     (INVOICE, 'Invoice'),
#     (RECEIPT, 'Reservation Receipt'),
#     (SUBSCRIPTION_RECEIPT, 'Subscription Receipt'),
#     (NEW_RESERVATION, 'New Reservation'),
#     (WELCOME, 'Pre-Arrival Welcome'),
#     (DEPARTURE, 'Departure'),
#     )
#
#     key = models.CharField(max_length=32, choices=KEYS)
#     text_body = models.TextField(verbose_name="The text body of the email")
#     html_body = models.TextField(blank=True, null=True, verbose_name="The html body of the email")


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
