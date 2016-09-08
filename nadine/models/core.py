import os
import uuid
import pprint
import traceback
import operator
import logging

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

from doors.keymaster.models import DoorEvent

logger = logging.getLogger(__name__)


GENDER_CHOICES = (
    ('U', 'Unknown'),
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

PAYMENT_CHOICES = (
    ('Bill', 'Billable'),
    ('Trial', 'Free Trial'),
    ('Waive', 'Payment Waived'),
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
            plan_members = Member.objects.members_by_plan(plan_name)
            if plan_members.count() > 0:
                group_list.append((plan_name, "%s Members" % plan_name))
        for g, d in sorted(MemberGroups.GROUP_DICT.items(), key=operator.itemgetter(0)):
            group_list.append((g, d))
        return group_list

    @staticmethod
    def get_members(group):
        if group == MemberGroups.ALL:
            return Member.objects.active_members()
        elif group == MemberGroups.HAS_DESK:
            return Member.objects.members_with_desks()
        elif group == MemberGroups.HAS_KEY:
            return Member.objects.members_with_keys()
        elif group == MemberGroups.HAS_MAIL:
            return Member.objects.members_with_mail()
        elif group == MemberGroups.NO_MEMBER_AGREEMENT:
            return Member.objects.missing_member_agreement()
        elif group == MemberGroups.NO_KEY_AGREEMENT:
            return Member.objects.missing_key_agreement()
        elif group == MemberGroups.NO_PHOTO:
            return Member.objects.missing_photo()
        elif group == MemberGroups.STALE_MEMBERSHIP:
            return Member.objects.stale_members()
        else:
            return None


class HowHeard(models.Model):

    """A record of how a member discovered the space"""
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class Industry(models.Model):

    """The type of work a member does"""
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


class MemberManager(models.Manager):

    def member_count(self, active_only):
        if active_only:
            return Member.objects.filter(memberships__start_date__isnull=False, memberships__end_date__isnull=True).count()
        else:
            return Member.objects.all().count()

    def active_members(self):
        return Member.objects.filter(id__in=Membership.objects.active_memberships().values('member'))

    def active_users(self):
        return User.objects.filter(id__in=Membership.objects.active_memberships().values('user'))
        #return self.active_members().values('user')

    def daily_members(self):
        return self.active_members().exclude(id__in=self.members_with_desks())

    def here_today(self, day=None):
        if not day:
            day = timezone.now().date()

        # The members who are on the network
        from arpwatch.arp import users_for_day_query
        arp_members_query = users_for_day_query(day=day)

        # The members who have signed in
        daily_members_query = Member.objects.filter(pk__in=DailyLog.objects.filter(visit_date=day).values('member__id'))

        # The members that have access a door
        door_query = DoorEvent.objects.users_for_day(day)
        door_members_query = Member.objects.active_members().filter(user__in=door_query.values('user'))

        combined_query = arp_members_query | daily_members_query | door_members_query
        return combined_query.distinct()

    def not_signed_in(self, day=None):
        if not day:
            day = timezone.now().date()

        signed_in = []
        for l in DailyLog.objects.filter(visit_date=day):
            signed_in.append(l.member)

        not_signed_in = []
        for member in self.here_today(day):
            if not member in signed_in and not member.has_desk(day):
                not_signed_in.append({'member':member, 'day':day})

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

    def active_member_emails(self, include_email2=False):
        emails = []
        for membership in Membership.objects.active_memberships():
            member = membership.member
            user = membership.user
            if user.email not in emails:
                emails.append(user.email)
            if include_email2 and member.email2 not in emails:
                emails.append(member.email2)
        return emails

    def exiting_members(self, day=None):
        if day == None:
            day = timezone.now()
        next_day = day + timedelta(days=1)

        # Exiting members are here today and gone tomorrow.  Pull up all the active
        # memberships for today and remove the list of active members tomorrow.
        today_memberships = Membership.objects.active_memberships(day)
        tomorrow_memberships = Membership.objects.active_memberships(next_day)
        exiting = today_memberships.exclude(member__in=tomorrow_memberships.values('member'))

        return Member.objects.filter(id__in=exiting.values('member'))

    def expired_slack_users(self):
        expired_users = []
        active_emails = self.active_member_emails(include_email2=True)
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
        recently_used = DailyLog.objects.filter(visit_date__gte=smd).values('member').distinct()
        memberships = Membership.objects.active_memberships().filter(start_date__lte=smd, has_desk=False)
        return Member.objects.filter(id__in=memberships.values('member')).exclude(id__in=recently_used)

    def missing_member_agreement(self):
        active_agmts = FileUpload.objects.filter(document_type=FileUpload.MEMBER_AGMT, user__in=self.active_users()).distinct()
        users_with_agmts = active_agmts.values('user')
        return self.active_members().exclude(user__in=users_with_agmts)

    def missing_key_agreement(self):
        active_agmts = FileUpload.objects.filter(document_type=FileUpload.KEY_AGMT, user__in=self.active_users()).distinct()
        users_with_agmts = active_agmts.values('user')
        return self.members_with_keys().exclude(user__in=users_with_agmts)

    def missing_photo(self):
        return self.active_members().filter(photo="")

    def invalid_billing(self):
        members = []
        for m in self.active_members():
            membership = m.active_membership()
            if membership and membership.monthly_rate > 0:
                if not m.has_valid_billing():
                    members.append(m)
        return members

    def recent_members(self, days):
        return Member.objects.filter(user__date_joined__gt=timezone.localtime(timezone.now()) - timedelta(days=days))

    def members_by_plan(self, plan):
        memberships = Membership.objects.active_memberships().filter(membership_plan__name=plan)
        return Member.objects.filter(id__in=memberships.values('member'))

    def members_by_plan_id(self, plan_id):
        memberships = Membership.objects.active_memberships().filter(membership_plan=plan_id)
        return Member.objects.filter(id__in=memberships.values('member'))

    def members_with_desks(self):
        memberships = Membership.objects.active_memberships().filter(has_desk=True)
        return Member.objects.filter(id__in=memberships.values('member'))

    def members_with_keys(self):
        memberships = Membership.objects.active_memberships().filter(has_key=True)
        return Member.objects.filter(id__in=memberships.values('member'))

    def members_with_mail(self):
        memberships = Membership.objects.active_memberships().filter(has_mail=True)
        return Member.objects.filter(id__in=memberships.values('member'))

    def members_by_neighborhood(self, hood, active_only=True):
        if active_only:
            return Member.objects.filter(neighborhood=hood).filter(memberships__isnull=False).filter(Q(memberships__end_date__isnull=True) | Q(memberships__end_date__gt=timezone.now().date())).distinct()
        else:
            return Member.objects.filter(neighborhood=hood)

    def managers(self, include_future=False):
        if hasattr(settings, 'TEAM_MEMBERSHIP_PLAN'):
            management_plan = MembershipPlan.objects.filter(name=settings.TEAM_MEMBERSHIP_PLAN).first()
            memberships = Membership.objects.active_memberships().filter(membership_plan=management_plan).distinct()
            if include_future:
                memberships = memberships | Membership.objects.future_memberships().filter(membership_plan=management_plan).distinct()
            return Member.objects.filter(id__in=memberships.values('member'))
        return None

    def unsubscribe_recent_dropouts(self):
        """Remove mailing list subscriptions from members whose memberships expired yesterday and they do not start a membership today"""
        from interlink.models import MailingList
        recently_expired = Member.objects.filter(memberships__end_date=timezone.now().date() - timedelta(days=1)).exclude(memberships__start_date=timezone.now().date())
        for member in recently_expired:
            MailingList.objects.unsubscribe_from_all(member.user)

    def search(self, search_string, active_only=False):
        terms = search_string.split()
        if len(terms) == 0:
            return None
        fname_query = Q(user__first_name__icontains=terms[0])
        lname_query = Q(user__last_name__icontains=terms[0])
        for term in terms[1:]:
            fname_query = fname_query | Q(user__first_name__icontains=term)
            lname_query = lname_query | Q(user__last_name__icontains=term)

        if active_only:
            active_members = self.active_members()
            return active_members.filter(fname_query | lname_query)

        return self.filter(fname_query | lname_query)

    def get_by_natural_key(self, user_id): return self.get(user__id=user_id)


def user_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return "user_photos/%s.%s" % (instance.user.username, ext.lower())


class Member(models.Model):
    MAX_PHOTO_SIZE = 1024

    """A person who has used the space and may or may not have a monthly membership"""
    objects = MemberManager()

    user = models.OneToOneField(User, blank=False)
    email2 = models.EmailField("Alternate Email", blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    phone2 = PhoneNumberField("Alternate Phone", blank=True, null=True)
    address1 = models.CharField(max_length=128, blank=True)
    address2 = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zipcode = models.CharField(max_length=5, blank=True)
    bio = models.TextField(blank=True, null=True)
    public_profile = models.BooleanField(default=False)
    url_personal = models.URLField(blank=True, null=True)
    url_professional = models.URLField(blank=True, null=True)
    url_facebook = models.URLField(blank=True, null=True)
    url_twitter = models.URLField(blank=True, null=True)
    url_linkedin = models.URLField(blank=True, null=True)
    url_aboutme = models.URLField(blank=True, null=True)
    url_github = models.URLField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="U")
    howHeard = models.ForeignKey(HowHeard, blank=True, null=True)
    #referred_by = models.ForeignKey(User, verbose_name="Referred By", related_name="referral", blank=True, null=True)
    industry = models.ForeignKey(Industry, blank=True, null=True)
    neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True)
    has_kids = models.NullBooleanField(blank=True, null=True)
    self_employed = models.NullBooleanField(blank=True, null=True)
    company_name = models.CharField(max_length=128, blank=True, null=True)
    promised_followup = models.DateField(blank=True, null=True)
    last_modified = models.DateField(auto_now=True, editable=False)
    photo = models.ImageField(upload_to=user_photo_path, blank=True, null=True)
    tags = TaggableManager(blank=True)
    valid_billing = models.NullBooleanField(blank=True, null=True)

    @property
    def first_name(self): return smart_str(self.user.first_name)

    @property
    def last_name(self): return smart_str(self.user.last_name)

    @property
    def email(self): return self.user.email

    @property
    def full_name(self):
        return '%s %s' % (smart_str(self.user.first_name), smart_str(self.user.last_name))

    def natural_key(self): return [self.user.id]

    def all_bills(self):
        """Returns all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
        from nadine.models.payment import Bill
        return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).order_by('-bill_date')

    def open_bills(self):
        """Returns all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
        from nadine.models.payment import Bill
        return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).filter(transactions=None).order_by('bill_date')

    def open_bill_amount(self):
        total = 0
        for b in self.open_bills():
            total = total + b.amount
        return total

    def open_bills_amount(self):
        """Returns the amount of all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
        from nadine.models.payment import Bill
        return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).filter(transactions=None).aggregate(models.Sum('amount'))['amount__sum']

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
        from nadine.models.payment import Bill
        bills = Bill.objects.filter(member=self)
        if len(bills) == 0:
            return None
        return bills[0]

    def membership_history(self):
        return Membership.objects.filter(member=self).order_by('-start_date', 'end_date')

    def membership_on_date(self, day):
        return Membership.objects.filter(member=self, start_date__lte=day).filter(Q(end_date__isnull=True) | Q(end_date__gte=day)).first()

    def last_membership(self):
        """Returns the latest membership, even if it has an end date, or None if none exists"""
        memberships = Membership.objects.filter(member=self).order_by('-start_date', 'end_date')[0:]
        if memberships == None or len(memberships) == 0:
            return None
        return memberships[0]

    def active_membership(self):
        for membership in self.membership_history():
            if membership.is_active():
                return membership
        return None

    def membership_for_day(self, day):
        return Membership.objects.active_memberships(target_date=day).filter(member=self).first()

    def activity_this_month(self, test_date=None):
        if not test_date:
            test_date = date.today()

        membership = self.active_membership()
        if membership:
            if membership.guest_of:
                # Return host's activity
                host = membership.guest_of
                return host.activity_this_month()
            month_start = membership.prev_billing_date(test_date)
        else:
            # Just go back one month from this date since there isn't a membership to work with
            month_start = test_date - MonthDelta(1)

        activity = []
        for m in [self] + self.guests():
            for l in DailyLog.objects.filter(member=m, payment='Bill', visit_date__gte=month_start):
                activity.append(l)
        for l in DailyLog.objects.filter(guest_of=self, payment='Bill', visit_date__gte=month_start):
            activity.append(l)
        return activity

    def activity(self):
        return DailyLog.objects.filter(member=self)

    def paid_count(self):
        return self.activity().filter(payment='Bill').count()

    def first_visit(self):
        if Membership.objects.filter(member=self).count() > 0:
            return Membership.objects.filter(member=self).order_by('start_date')[0].start_date
        else:
            if DailyLog.objects.filter(member=self).count() > 0:
                return DailyLog.objects.filter(member=self).order_by('visit_date')[0].visit_date
            else:
                return None

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

    def is_anniversary(self):

        return

    def host_daily_logs(self):
        return DailyLog.objects.filter(guest_of=self).order_by('-visit_date')

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
        if DailyLog.objects.filter(member=self).count() > 0:
            return DailyLog.objects.filter(member=self).latest('visit_date').visit_date
        else:
            if Membership.objects.filter(member=self, end_date__isnull=False).count() > 0:
                return Membership.objects.filter(member=self, end_date__isnull=False).latest('end_date').end_date
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
        drop_ins = DailyLog.objects.filter(member=self).count()
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
        if m and m.is_active() and m.guest_of:
            return m.guest_of
        return None

    def has_valid_billing(self):
        host = self.is_guest()
        if host:
            return host.has_valid_billing()
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

    def guests(self):
        guests = []
        for membership in Membership.objects.filter(guest_of=self):
            if membership.is_active():
                guests.append(membership.member)
        return guests

    def deposits(self):
        return SecurityDeposit.objects.filter(member=self)

    def __str__(self): return '%s %s' % (smart_str(self.user.first_name), smart_str(self.user.last_name))

    def auto_bill_enabled(self):
        api = PaymentAPI()
        return api.auto_bill_enabled(self.user.username)

    def member_notes(self):
        return MemberNote.objects.filter(member=self)

    def special_days(self):
        return SpecialDay.objects.filter(member=self)

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
        bills = Bill.objects.filter(member=self)
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
post_save.connect(profile_save_callback, sender=Member)

def user_save_callback(sender, **kwargs):
    user = kwargs['instance']
    # Make certain we have a Member record
    if not Member.objects.filter(user=user).count() > 0:
        Member.objects.create(user=user)
post_save.connect(user_save_callback, sender=User)

# Add some handy methods to Django's User object
User.get_profile = lambda self: Member.objects.get_or_create(user=self)[0]
User.get_emergency_contact = lambda self: EmergencyContact.objects.get_or_create(user=self)[0]
User.profile = property(User.get_profile)

@receiver(post_save, sender=Member)
def size_images(sender, instance, **kwargs):
    if instance.photo:
        image = Image.open(instance.photo)
        old_x, old_y = image.size
        if old_x > Member.MAX_PHOTO_SIZE or old_y > Member.MAX_PHOTO_SIZE:
            print("Resizing photo for %s" % instance.user.username)
            if old_y > old_x:
                new_y = Member.MAX_PHOTO_SIZE
                new_x = int((float(new_y) / old_y) * old_x)
            else:
                new_x = Member.MAX_PHOTO_SIZE
                new_y = int((float(new_x) / old_x) * old_y)
            new_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            new_image.save(instance.photo.path, image.format)
        image.close()


class EmergencyContact(models.Model):
    user = models.OneToOneField(User, blank=False)
    name = models.CharField(max_length=254, blank=True)
    relationship = models.CharField(max_length=254, blank=True)
    phone = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True)

def emergency_callback_save_callback(sender, **kwargs):
    contact = kwargs['instance']
    contact.last_updated = timezone.now()
pre_save.connect(emergency_callback_save_callback, sender=EmergencyContact)


class XeroContact(models.Model):
    user = models.OneToOneField(User, related_name="xero_contact")
    xero_id = models.CharField(max_length=64)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s - %s' % (self.user.username, self.xero_id)

class DailyLog(models.Model):

    """A visit by a member"""
    user = models.ForeignKey(User)
    member = models.ForeignKey(Member, verbose_name="Member", unique_for_date="visit_date", related_name="daily_logs")
    visit_date = models.DateField("Date")
    payment = models.CharField("Payment", max_length=5, choices=PAYMENT_CHOICES)
    guest_of = models.ForeignKey(Member, verbose_name="Guest Of", related_name="guest_of", blank=True, null=True)
    note = models.CharField("Note", max_length=128, blank="True")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s' % (self.visit_date, self.member)

    def get_admin_url(self):
        return urlresolvers.reverse('admin:nadine_dailylog_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "Daily Log"
        ordering = ['-visit_date', '-created']


def sign_in_callback(sender, **kwargs):
    log = kwargs['instance']
    from nadine.models.alerts import MemberAlert
    MemberAlert.objects.trigger_sign_in(log.user)
post_save.connect(sign_in_callback, sender=DailyLog)


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

    def create_with_plan(self, member, start_date, end_date, membership_plan, rate=-1, guest_of=None):
        if rate < 0:
            rate = membership_plan.monthly_rate
        self.create(member=member, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
                    monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
                    has_desk=membership_plan.has_desk, guest_of=guest_of)

    def active_memberships(self, target_date=None):
        if not target_date:
            target_date = timezone.now().date()
        current = Q(start_date__lte=target_date)
        unending = Q(end_date__isnull=True)
        future_ending = Q(end_date__gte=target_date)
        return self.filter(current & (unending | future_ending)).distinct()

    def future_memberships(self):
        today = timezone.now().date()
        return self.filter(start_date__gte=today)


class Membership(models.Model):

    """A membership level which is billed monthly"""
    user = models.ForeignKey(User)
    member = models.ForeignKey(Member, related_name="memberships")
    membership_plan = models.ForeignKey(MembershipPlan, null=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(blank=True, null=True, db_index=True)
    monthly_rate = models.IntegerField(default=0)
    dropin_allowance = models.IntegerField(default=0)
    daily_rate = models.IntegerField(default=0)
    has_desk = models.BooleanField(default=False)
    has_key = models.BooleanField(default=False)
    has_mail = models.BooleanField(default=False)
    guest_of = models.ForeignKey(Member, blank=True, null=True, related_name="monthly_guests")

    objects = MembershipManager()

    def save(self, *args, **kwargs):
        if Membership.objects.active_memberships(self.start_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
            raise Exception('Already have a Membership for that start date')
        if self.end_date and Membership.objects.active_memberships(self.end_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
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
        return Membership.objects.filter(member=self.member, end_date=self.start_date - timedelta(days=1)).count() > 0

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
        if self.guest_of:
            m = self.guest_of.active_membership()
            if m:
                return m.dropin_allowance
            else:
                return 0
        return self.dropin_allowance

    def __str__(self):
        return '%s - %s - %s' % (self.start_date, self.member, self.membership_plan)

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
    member = models.ForeignKey('Member', null=True)
    recipient = models.EmailField()
    subject = models.CharField(max_length=128, blank=True, null=True)
    success = models.NullBooleanField(blank=False, null=False, default=False)
    note = models.TextField(blank=True, null=True)

    def __str__(self): return '%s: %s' % (self.created, self.recipient)


class SecurityDeposit(models.Model):
    user = models.ForeignKey(User)
    member = models.ForeignKey('Member', blank=False, null=False)
    received_date = models.DateField()
    returned_date = models.DateField(blank=True, null=True)
    amount = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=128, blank=True, null=True)


class SpecialDay(models.Model):
    user = models.ForeignKey(User)
    member = models.ForeignKey('Member', blank=False, null=False)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    day = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.CharField(max_length=128, blank=True, null=True)


class MemberNote(models.Model):
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, related_name='+')
    member = models.ForeignKey('Member', blank=False, null=False)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s - %s: %s' % (self.created.date(), self.member, self.note)


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

# Copyright 2014 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
