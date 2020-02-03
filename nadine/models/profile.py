import os
import sys
import uuid
import pprint
import random
import traceback
import operator
import logging
import hashlib
import pytz
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.contrib import admin
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.encoding import smart_str
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.contrib.sites.models import Site

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

# imports for signals
import django.dispatch
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from PIL import Image

from nadine.settings import TIME_ZONE
from nadine.utils.payment_api import PaymentAPI
from nadine.utils.slack_api import SlackAPI
from nadine.models.core import GENDER_CHOICES, HowHeard, Industry, Neighborhood, Website, URLType
from nadine.models.membership import Membership, IndividualMembership, ResourceSubscription, SecurityDeposit
from nadine.models.resource import Resource
from nadine.models.usage import CoworkingDay
from nadine.models.organization import Organization
from nadine import email

from doors.keymaster.models import DoorEvent

logger = logging.getLogger(__name__)


def user_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return "user_photos/%s.%s" % (instance.user.username, ext.lower())


def user_file_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    if ext:
        filename = "file_uploads/%s/%s.%s" % (instance.user.username, uuid.uuid4(), ext)
    else:
        filename = "file_uploads/%s/%s" % (instance.user.username, uuid.uuid4())
    return filename


###############################################################################
# Models and Managers
###############################################################################


class UserQueryHelper():

    def active_individual_members(self, target_date=None):
        individual_memberships = Membership.objects.active_individual_memberships(target_date)
        return User.objects.filter(id__in=individual_memberships.values('individualmembership__user'))

    def active_organization_members(self, target_date=None):
        organization_memberships = Membership.objects.active_organization_memberships(target_date)
        return User.objects.filter(id__in=organization_memberships.values('organizationmembership__organization__organizationmember__user'))

    def active_members(self, target_date=None):
        individual_members = self.active_individual_members(target_date)
        organization_members = self.active_organization_members(target_date)
        combined_query = individual_members | organization_members
        return combined_query.distinct()

    def payers(self, target_date=None):
        ''' Return a set of Users that are paying for the active memberships '''
        # I tried to make this method as easy to read as possible. -- JLS
        # This joins the following sets:
        #   Individuals paying for their own membership,
        #   Organization leads of active organizations,
        #   Users paying for other's memberships
        active_paid_subscriptions = ResourceSubscription.objects.active_subscriptions(target_date).filter(monthly_rate__gt=0)
        paid_by_self = active_paid_subscriptions.filter(paid_by__isnull=True)

        paid_by_other = active_paid_subscriptions.filter(paid_by__isnull=False)
        other_payers = paid_by_other.annotate(payer=F('paid_by')).values('payer')

        is_individual_membership = Q(membership__individualmembership__isnull=False)
        individual_payers = paid_by_self.filter(is_individual_membership).annotate(payer=F('membership__individualmembership__user')).values('payer')

        is_organizaion_membership = Q(membership__organizationmembership__isnull=False)
        organization_leads = paid_by_self.filter(is_organizaion_membership).annotate(payer=F('membership__organizationmembership__organization__lead')).values('payer')

        combined_set = (individual_payers | organization_leads | other_payers)
        return User.objects.filter(id__in=combined_set).distinct()

    def invalid_billing(self):
        return self.payers().filter(profile__valid_billing=False)

    def here_today(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()

        # The members who are on the network
        from arpwatch.arp import users_for_day_query
        arp_members_query = users_for_day_query(day=target_date).distinct()

        # The members who have signed in
        daily_members_query = User.objects.filter(id__in=CoworkingDay.objects.filter(visit_date=target_date).values('user__id')).distinct()

        # The members that have accessed a door
        door_query = DoorEvent.objects.users_for_day(target_date)
        door_members_query = User.helper.active_members().filter(id__in=door_query.values('user__id'))

        combined_query = arp_members_query | daily_members_query | door_members_query
        return combined_query.distinct()

    def not_signed_in(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()

        signed_in = []
        for l in CoworkingDay.objects.filter(visit_date=target_date):
            signed_in.append(l.user)

        not_signed_in = []
        for u in self.here_today(target_date):
            if not u in signed_in and not u.membership.has_desk(target_date):
                not_signed_in.append({'user':u, 'day':target_date})

        return not_signed_in

    def not_signed_in_since(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        not_signed_in = []

        d = localtime(now()).date()
        while target_date <= d:
            not_signed_in.extend(self.not_signed_in(d))
            d = d - timedelta(days=1)

        return not_signed_in

    def exiting_members(self, target_date=None):
        if target_date == None:
            target_date = localtime(now())

        # Exiting members are here today and gone tomorrow.  Pull up all the active
        # memberships for today and remove the list of active members tomorrow.
        today_memberships = self.active_members(target_date)
        tomorrow_memberships = self.active_members(target_date + timedelta(days=1))
        return today_memberships.exclude(id__in=tomorrow_memberships.values('id'))

    def active_member_emails(self):
        return EmailAddress.objects.filter(user__in=self.active_members()).values_list('email', flat=True)

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
        three_months_ago = localtime(now()) - relativedelta(months=3)
        return three_months_ago

    def stale_members(self):
        smd = self.stale_member_date()
        recently_used = Q(id__in=CoworkingDay.objects.filter(visit_date__gte=smd).values('user').distinct())
        has_desk = Q(id__in=self.members_with_desks().values('id'))
        return self.active_members().exclude(has_desk).exclude(recently_used).order_by('first_name')

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

    def members_by_package(self, package_name, target_date=None):
        active_subscriptions = ResourceSubscription.objects.active_subscriptions_with_username(target_date).filter(package_name=package_name)
        return User.objects.filter(username__in=active_subscriptions.values('username'))

    def members_by_resource(self, resource, target_date=None):
        active_subscriptions = ResourceSubscription.objects.active_subscriptions_with_username(target_date).filter(resource=resource)
        return User.objects.filter(username__in=active_subscriptions.values('username'))

    def members_with_desks(self, target_date=None):
        ''' Return a set of users with an active 'desk' subscription. '''
        return self.members_by_resource(Resource.objects.desk_resource, target_date).order_by('first_name')

    def members_with_keys(self, target_date=None):
        ''' Return a set of users with an active 'key' subscription. '''
        return self.members_by_resource(Resource.objects.key_resource, target_date).order_by('first_name')

    def members_with_mail(self, target_date=None):
        ''' Return a set of users with an active 'mail' subscription. '''
        return self.members_by_resource(Resource.objects.mail_resource, target_date).order_by('first_name')

    def members_by_neighborhood(self, hood, active_only=True):
        if active_only:
            return self.active_members().filter(profile__neighborhood=hood)
        else:
            return User.objects.filter(profile__neighborhood=hood)

    def members_with_tag(self, tag):
        return self.active_members().filter(profile__tags__name__in=[tag])

    def managers(self, include_future=False):
        ''' Return the users with active or future subscriptions of type TEAM_MEMBERSHIP_PACKAGE '''
        if hasattr(settings, 'TEAM_MEMBERSHIP_PACKAGE'):
            management_package = settings.TEAM_MEMBERSHIP_PACKAGE
            subscriptions = ResourceSubscription.objects.active_subscriptions().filter(package_name=management_package).distinct()
            if include_future:
                subscriptions = subscriptions | ResourceSubscription.objects.future_subscriptions().filter(package_name=management_package).distinct()
            return User.objects.filter(id__in=subscriptions.values('membership__individualmembership__user')).distinct()
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

        return user_query.order_by('first_name', 'last_name')

    def by_email(self, email):
        email_address = EmailAddress.objects.filter(email=email).first()
        if email_address:
            return email_address.user
        return None


class UserProfile(models.Model):
    MAX_PHOTO_SIZE = 1024

    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=False, related_name="profile", on_delete=models.CASCADE)
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
    pronouns = models.CharField(max_length=64, blank=True, null=True)
    howHeard = models.ForeignKey(HowHeard, blank=True, null=True, on_delete=models.CASCADE)
    #referred_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Referred By", related_name="referral", blank=True, null=True, on_delete=models.CASCADE)
    industry = models.ForeignKey(Industry, blank=True, null=True, on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True, on_delete=models.CASCADE)
    has_kids = models.NullBooleanField(blank=True, null=True)
    self_employed = models.NullBooleanField(blank=True, null=True)
    last_modified = models.DateField(auto_now=True, editable=False)
    photo = models.ImageField(upload_to=user_photo_path, blank=True, null=True)
    tags = TaggableManager(blank=True)
    valid_billing = models.NullBooleanField(blank=True, null=True)
    websites = models.ManyToManyField(Website, blank=True)

    @property
    def url_personal(self):
        return self.websites.filter(url_type__name="personal").first()

    @property
    def url_professional(self):
        return self.websites.filter(url_type__name="professional").first()

    @property
    def url_facebook(self):
        return self.websites.filter(url_type__name="facebook").first()

    @property
    def url_twitter(self):
        return self.websites.filter(url_type__name="twitter").first()

    @property
    def url_linkedin(self):
        return self.websites.filter(url_type__name="linkedin").first()

    @property
    def url_github(self):
        return self.websites.filter(url_type__name="github").first()

    def save_url(self, url_type, url_value):
        if url_type and url_value:
            w = self.websites.filter(url_type__name=url_type).first()
            if w:
                w.url = url_value
                w.save()
            else:
                t = URLType.objects.get(name=url_type)
                self.websites.create(url_type=t, url=url_value)

    def active_organization_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        future = Q(end_date__isnull=True)
        unending = Q(end_date__gte=target_date)
        return self.user.organizationmember_set.filter(start_date__lte=target_date).filter(future | unending)

    def past_organization_memberships(self, target_date=None):
        if not target_date:
            target_date = localtime(now()).date()
        return self.user.organizationmember_set.filter(end_date__lte=target_date)

    def active_organizations(self, target_date=None):
        active = self.active_organization_memberships(target_date)
        return Organization.objects.filter(id__in=active.values('organization'))

    def outstanding_bills(self):
        """Returns all outstanding bills for this user """
        from nadine.models.billing import UserBill
        return UserBill.objects.outstanding().filter(user=self.user)

    @property
    def outstanding_amount(self):
        """Returns total of all open bills for this user """
        total = 0
        for b in self.outstanding_bills():
            total += b.total_owed
        return total

    def open_xero_invoices(self):
        from nadine.utils.xero_api import XeroAPI
        xero_api = XeroAPI()
        return xero_api.get_open_invoices(self.user)

    def pay_bills_form(self):
        from nadine.forms import PaymentForm
        return PaymentForm(initial={'username': self.user.username, 'amount': self.open_bills_amount})

    def days_used(self, target_date=None):
        membership = Membership.objects.for_user(self.user, target_date)
        days = membership.coworking_days_in_period(target_date)
        billable = days.filter(payment="Bill")
        allowed = membership.coworking_day_allowance(target_date)
        return (days.count(), allowed, billable.count())

    def all_emails(self):
        # Done in two queries so that the primary email address is always on top.
        primary = self.user.emailaddress_set.filter(is_primary=True)
        non_primary = self.user.emailaddress_set.filter(is_primary=False)
        return list(primary) + list(non_primary)

    def non_primary_emails(self):
        return self.user.emailaddress_set.filter(is_primary=False)

    def duration(self):
        return relativedelta(localtime(now()).date(), self.first_visit)

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
        return list(files.values())

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

    @property
    def first_visit(self):
        first_visit = date.max
        first_day = CoworkingDay.objects.filter(user=self.user).order_by('visit_date').first()
        if first_day:
            if first_day.visit_date < first_visit:
                first_visit = first_day.visit_date
        individual_membership = IndividualMembership.objects.get(user=self.user)
        first_subscription = ResourceSubscription.objects.filter(membership=individual_membership).order_by('start_date').first()
        if first_subscription:
            if first_subscription.start_date < first_visit:
                first_visit = first_subscription.start_date
        # TODO - pull the first time we saw them in an organization
        if first_visit < date.max:
            return first_visit
        return None

    @property
    def last_visit(self):
        last_visit = date.min
        last_day = CoworkingDay.objects.filter(user=self.user).order_by('visit_date').last()
        if last_day:
            if last_day.visit_date > last_visit:
                last_visit = last_day.visit_date
        individual_membership = IndividualMembership.objects.get(user=self.user)
        last_subscription = ResourceSubscription.objects.filter(membership=individual_membership).order_by('start_date').last()
        if last_subscription and last_subscription.end_date:
            if last_subscription.end_date > last_visit:
                last_visit = last_subscription.end_date
        # TODO - pull the last time we saw them in an organization
        if last_visit > date.min:
            return last_visit
        return None

    @property
    def membership_type(self):
        membership_type = ""
        membership = Membership.objects.for_user(self.user)
        if membership:
            if not membership.is_active():
                membership_type += "Ex "
            if membership.is_organization:
                membership_type += "Org "

            # Evaluate our package name
            package_name = membership.package_name()
            if package_name:
                membership_type += package_name
                if not membership.package_is_pure():
                    membership_type += " *"
            if len(membership_type) > 0:
                return membership_type

        # Now check daily logs
        drop_ins = CoworkingDay.objects.filter(user=self.user).count()
        if drop_ins == 0:
            return "New User"
        elif drop_ins == 1:
            return "First Day"
        else:
            return "Drop-in"

    def active_subscriptions(self, target_date=None):
        return ResourceSubscription.objects.active_subscriptions_with_username(target_date).filter(username=self.user.username)

    def is_active(self, target_date=None):
        return self.active_subscriptions(target_date).count() > 0

    def is_guest(self, target_date=None):
        for s in self.active_subscriptions(target_date):
            if s.paid_by is not None:
                return True
        return False

    def hosts(self, target_date=None):
        hosts = []
        for s in self.active_subscriptions(target_date):
            if s.paid_by is not None and s.paid_by not in hosts:
                hosts.append(s.paid_by)
        return hosts

    def guests(self, target_date=None):
        guests = []
        for subscription in ResourceSubscription.objects.active_subscriptions_with_username(target_date).filter(paid_by=self.user):
            guest = User.objects.get(username=subscription.username)
            if guest not in guests:
                guests.append(guest)
        return guests

    def has_valid_billing(self, lookup_new_card=True):
        hosts = self.hosts()
        if hosts:
            for host in hosts:
                if not host.profile.has_valid_billing():
                    # If just one host has invalid billing...
                    return False
            # All hosts have valid billing
            return True

        if self.valid_billing is None and lookup_new_card:
            logger.debug("%s: Null Valid Billing.  Looking for new card..." % self)
            if self.has_new_card():
                logger.debug("%s: Found new card.  Marking billing valid." % self)
                self.valid_billing = True
                self.save()
            else:
                return False
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

    def auto_bill_enabled(self):
        if not hasattr(settings, 'USA_EPAY_SOAP_KEY'):
            return None
        api = PaymentAPI()
        return api.auto_bill_enabled(self.user.username)

    def membership_days(self):
        total_days = 0
        for membership in self.membership_history():
            end = membership.end_date
            if not end:
                end = localtime(now()).date()
            diff = end - membership.start_date
            days = diff.days
            total_days = total_days + days
        return total_days

    def average_bill(self):
        from nadine.models.billing import UserBill
        bills = UserBill.objects.filter(user=self.user)
        if bills:
            bill_totals = 0
            for b in bills:
                bill_totals = bill_totals + b.amount
            return bill_totals / len(bills)
        return 0

    def is_manager(self):
        if self.user.is_staff: return True
        managers = User.helper.managers(include_future=True)
        return self.user in managers

    def __str__(self): return '%s %s' % (smart_str(self.user.first_name), smart_str(self.user.last_name))

    def get_absolute_url(self):
        return reverse('member:profile:view', kwargs={'username': self.user.username})

    def get_staff_url(self):
        return reverse('staff:members:detail', kwargs={'username': self.user.username})

    class Meta:
        app_label = 'nadine'
        ordering = ['user__first_name', 'user__last_name']
        get_latest_by = "last_modified"


class EmailAddress(models.Model):
    """An e-mail address for a Django User. Users may have more than one
    e-mail address. The address that is on the user object itself as the
    email property is considered to be the primary address, for which there
    should also be an EmailAddress object associated with the user.

    Pulled from https://github.com/scott2b/django-multimail
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(max_length=100, unique=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    verif_key = models.CharField(max_length=40)
    verified_ts = models.DateTimeField(default=None, null=True, blank=True)
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    remote_host = models.CharField(max_length=255, null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
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
        random.seed(datetime.now())
        salt = random.randint(0, sys.maxsize)
        salted_email = "%s%s" % (salt, self.email)
        self.verif_key = hashlib.sha1(salted_email.encode('utf-8')).hexdigest()
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
            verify_link = "https://" + site.domain + uri
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


class EmergencyContact(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=254, blank=True)
    relationship = models.CharField(max_length=254, blank=True)
    phone = PhoneNumberField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s' % (self.user.username, self.name)


class XeroContact(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="xero_contact", on_delete=models.CASCADE)
    xero_id = models.CharField(max_length=64)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s - %s' % (self.user.username, self.xero_id)


class SentEmailLog(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
    recipient = models.EmailField()
    subject = models.CharField(max_length=128, blank=True, null=True)
    success = models.NullBooleanField(blank=False, null=False, default=False)
    note = models.TextField(blank=True, null=True)

    def __str__(self): return '%s: %s' % (self.created, self.recipient)


class SpecialDay(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    month = models.PositiveSmallIntegerField(blank=True, null=True)
    day = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.CharField(max_length=128, blank=True, null=True)


class MemberNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='+', on_delete=models.CASCADE)
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

    objects = FileUploadManager()
    uploadTS = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    content_type = models.CharField(max_length=64)
    file = models.FileField(upload_to=user_file_upload_path, blank=False)
    document_type = models.CharField(max_length=200, choices=DOC_TYPES, default=None, null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="uploaded_by", on_delete=models.CASCADE)

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

    def __str__(self):
        return '%s - %s: %s' % (self.uploadTS.date(), self.user, self.name)


###############################################################################
# User Hooks
###############################################################################


# Like a ModelManager but since this is on the User model I needed
# to make it something different
User.helper = UserQueryHelper()

# Create a handy method on User to get an EmergencyContact
User.get_emergency_contact = lambda self: EmergencyContact.objects.get_or_create(user=self)[0]

# Method on User to get MemberNotes
User.get_member_notes = lambda self: MemberNote.objects.filter(user=self)


###############################################################################
# Call Backs
###############################################################################


@receiver(post_save, sender=User)
def user_save_callback(sender, **kwargs):
    user = kwargs['instance']
    # Make certain we have a Profile and IndividualMembership
    if not UserProfile.objects.filter(user=user).count() > 0:
        UserProfile.objects.create(user=user)
    from nadine.models.membership import IndividualMembership
    if not IndividualMembership.objects.filter(user=user).count() > 0:
        IndividualMembership.objects.create(user=user)


@receiver(post_save, sender=UserProfile)
def size_images(sender, instance, **kwargs):
    if instance.photo:
        image = Image.open(instance.photo)
        old_x, old_y = image.size
        if old_x > UserProfile.MAX_PHOTO_SIZE or old_y > UserProfile.MAX_PHOTO_SIZE:
            if old_y > old_x:
                new_y = UserProfile.MAX_PHOTO_SIZE
                new_x = int((float(new_y) / old_y) * old_x)
            else:
                new_x = UserProfile.MAX_PHOTO_SIZE
                new_y = int((float(new_x) / old_x) * old_y)
            new_image = image.resize((new_x, new_y), Image.ANTIALIAS)
            new_image.save(instance.photo.path, image.format)
        image.close()


@receiver(post_save, sender=User)
def sync_primary_callback(sender, **kwargs):
    user = kwargs['instance']
    try:
        email_address = EmailAddress.objects.get(email=user.email)
    except EmailAddress.DoesNotExist:
        email_address = EmailAddress(user=user, email=user.email)
        email_address.save(verify=False)
    email_address.set_primary()


@receiver(pre_save, sender=EmergencyContact)
def emergency_callback_save_callback(sender, **kwargs):
    contact = kwargs['instance']
    contact.last_updated = localtime(now())


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
