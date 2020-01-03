

import logging

from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save
from django.utils.timezone import localtime, now
from django.conf import settings

from comlink.models import MailingList

from nadine.models.profile import UserProfile, FileUpload
from nadine.models.membership import Membership, IndividualMembership, ResourceSubscription
from nadine.models.usage import CoworkingDay
from nadine.models.resource import Resource

logger = logging.getLogger(__name__)


#######################################################################
# Signals for every Trigger Action
#######################################################################

sign_in = Signal(providing_args=["user"])
profile_save = Signal(providing_args=["user"])
file_upload = Signal(providing_args=["user"])
change_membership = Signal(providing_args=["user"])
new_membership = Signal(providing_args=["user"])
ending_membership = Signal(providing_args=["user"])
new_desk_membership = Signal(providing_args=["user"])
ending_desk_membership = Signal(providing_args=["user"])
new_key_membership = Signal(providing_args=["user"])
ending_key_membership = Signal(providing_args=["user"])
new_mail_membership = Signal(providing_args=["user"])
ending_mail_membership = Signal(providing_args=["user"])


#######################################################################
# Member Alert Manager
#######################################################################

class MemberAlertManager(models.Manager):

    def create_if_not_open(self, user, key):
        ''' Create the alert if there isn't already an open one. '''
        unresolved = self.filter(user=user, key=key, resolved_ts__isnull=True, muted_ts__isnull=True)
        if unresolved.count() == 0:
            MemberAlert.objects.create(user=user, key=key)
            return True
        return False

    def create_if_new(self, user, key, new_since=None):
        ''' Create the alert if there are no alerts since the given date. '''
        old_alerts = MemberAlert.objects.filter(user=user, key=key)
        if new_since:
            old_alerts = old_alerts.filter(created_ts__gte=new_since)
        if old_alerts.count() == 0:
            return MemberAlert.objects.create_if_not_open(user=user, key=key)
        return False

    def unresolved(self, key, active_only=True):
        unresolved = self.filter(key=key, resolved_ts__isnull=True, muted_ts__isnull=True)
        # Persistent alerts apply even if a member is inactive
        persistent = key in MemberAlert.PERSISTENT_ALERTS
        if active_only and not persistent:
            active_users = User.helper.active_members()
            return unresolved.filter(user__in=active_users)
        return unresolved

    #######################################################################
    # Actions that need handeling
    #######################################################################

    def handle_periodic_check(self):
        logger.debug("handle_periodic_check")

        # Check for exiting members in the coming week
        exit_date = localtime(now()) + timedelta(days=5)
        exiting_members = User.helper.exiting_members(exit_date)
        for u in exiting_members:
            # Only trigger exiting membership if no exit alerts were created in the last week
            start = localtime(now()) - timedelta(days=5)
            if MemberAlert.objects.filter(user=u, key__in=MemberAlert.PERSISTENT_ALERTS, created_ts__gte=start).count() == 0:
                self.handle_ending_membership(u, exit_date)

        # Check for stale membership
        smd = User.helper.stale_member_date()
        for u in User.helper.stale_members():
            existing_alerts = MemberAlert.objects.filter(user=u, key=MemberAlert.STALE_MEMBER, created_ts__gte=smd)
            if not existing_alerts:
                MemberAlert.objects.create_if_not_open(user=u, key=MemberAlert.STALE_MEMBER)

        # Check for one month old memberships
        for u in User.helper.active_members():
            duration = u.profile.duration()
            if not duration.years and duration.months == 1:
                MemberAlert.objects.create_if_new(user=u, key=MemberAlert.ONE_MONTH)

    def handle_change_membership(self, user):
        logger.debug("handle_change_membership: %s" % user)
        change_membership.send(sender=self.__class__, user=user)

    def handle_ending_membership(self, user, target_date=None):
        logger.debug("handle_ending_membership: %s, %s" % (user, target_date))
        ending_membership.send(sender=self.__class__, user=user)
        if target_date == None:
            target_date = localtime(now())

        # If they have a photo, take it down and stop nagging us to take one
        if user.profile.photo:
            user.profile.resolve_alerts(MemberAlert.POST_PHOTO)
            MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.REMOVE_PHOTO)

    def handle_new_membership(self, user):
        logger.debug("handle_new_membership: %s" % user)
        new_membership.send(sender=self.__class__, user=user)

        # Pull a bunch of data so we don't keep hitting the database
        open_alerts = user.profile.alerts_by_key(include_resolved=False)
        all_alerts = user.profile.alerts_by_key(include_resolved=True)
        existing_files = user.profile.files_by_type()

        # Member Information
        if not FileUpload.MEMBER_INFO in existing_files:
            if not MemberAlert.PAPERWORK in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.PAPERWORK)
            if not MemberAlert.MEMBER_INFO in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.MEMBER_INFO)

        # Membership Agreement
        if not FileUpload.MEMBER_AGMT in existing_files:
            if not MemberAlert.MEMBER_AGREEMENT in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.MEMBER_AGREEMENT)

        # User Photo
        if not user.profile.photo:
            if not MemberAlert.TAKE_PHOTO in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.TAKE_PHOTO)
            if not MemberAlert.UPLOAD_PHOTO in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.UPLOAD_PHOTO)
        if not MemberAlert.POST_PHOTO in open_alerts:
            MemberAlert.objects.create(user=user, key=MemberAlert.POST_PHOTO)

        # New Member Orientation
        if not MemberAlert.ORIENTATION in all_alerts:
            MemberAlert.objects.create(user=user, key=MemberAlert.ORIENTATION)

    def handle_profile_save(self, user):
        logger.debug("handle_profile_save: %s" % user)
        profile_save.send(sender=self.__class__, user=user)

        # Remove the Photo from the wall if we have one
        if user.profile.photo:
            user.profile.resolve_alerts(MemberAlert.TAKE_PHOTO)
            user.profile.resolve_alerts(MemberAlert.UPLOAD_PHOTO)

    def handle_file_upload(self, user):
        logger.debug("handle_file_upload: %s" % user)
        file_upload.send(sender=self.__class__, user=user)

        existing_files = user.profile.files_by_type()

        # Resolve Member Info alert if the file is now present
        if FileUpload.MEMBER_INFO in existing_files:
            user.profile.resolve_alerts(MemberAlert.PAPERWORK)
            user.profile.resolve_alerts(MemberAlert.MEMBER_INFO)

        # Resolve Member Agreement alert if the file is now present
        if FileUpload.MEMBER_AGMT in existing_files:
            user.profile.resolve_alerts(MemberAlert.MEMBER_AGREEMENT)

        # Resolve Key Agreement alert if the file is now present
        if FileUpload.KEY_AGMT in existing_files:
            user.profile.resolve_alerts(MemberAlert.KEY_AGREEMENT)

    def handle_sign_in(self, user):
        logger.debug("handle_sign_in: %s" % user)
        sign_in.send(sender=self.__class__, user=user)

        # If they have signed in, they are not stale anymore
        user.profile.resolve_alerts(MemberAlert.STALE_MEMBER)

    def handle_new_desk(self, user):
        logger.debug("handle_new_desk: %s" % user)
        new_desk_membership.send(sender=self.__class__, user=user)

        # No need to return the desk key since their new membership has a desk
        user.profile.resolve_alerts(MemberAlert.RETURN_DESK_KEY)

        # A desk comes with a cabinet
        MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.ASSIGN_CABINET)

    def handle_ending_desk(self, user, end_date):
        logger.debug("handle_ending_desk: %s" % user)
        ending_desk_membership.send(sender=self.__class__, user=user)

        # Get the cabinet key back
        user.profile.resolve_alerts(MemberAlert.ASSIGN_CABINET)
        MemberAlert.objects.create_if_new(user=user, key=MemberAlert.RETURN_DESK_KEY)

    def handle_new_key(self, user):
        logger.debug("handle_new_key: %s" % user)
        new_key_membership.send(sender=self.__class__, user=user)

        # No need to return the door key if they now have a key
        user.profile.resolve_alerts(MemberAlert.RETURN_DOOR_KEY)

        # Check for a key agreement
        if not FileUpload.KEY_AGMT in user.profile.files_by_type():
            MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.KEY_AGREEMENT)

    def handle_ending_key(self, user, end_date):
        logger.debug("handle_ending_key: %s" % user)
        ending_key_membership.send(sender=self.__class__, user=user)

        # They need to return their door key
        MemberAlert.objects.create_if_new(user, MemberAlert.RETURN_DOOR_KEY, end_date)

    def handle_new_mail(self, user):
        logger.debug("handle_new_mail: %s" % user)
        new_mail_membership.send(sender=self.__class__, user=user)

        # No need to remove the mailbox since their new membership has mail
        user.profile.resolve_alerts(MemberAlert.REMOVE_MAILBOX)

        # Assign a mailbox
        MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.ASSIGN_MAILBOX)

    def handle_ending_mail(self, user, end_date):
        logger.debug("handle_ending_mail: %s" % user)
        ending_mail_membership.send(sender=self.__class__, user=user)

        # We don't need to assign a mailbox if they are ending it
        user.profile.resolve_alerts(MemberAlert.ASSIGN_MAILBOX)
        MemberAlert.objects.create_if_new(user=user, key=MemberAlert.REMOVE_MAILBOX)


############################################################################
# Call Backs
############################################################################


@receiver(post_save, sender=UserProfile)
def profile_save_callback(sender, **kwargs):
    profile = kwargs['instance']
    MemberAlert.objects.handle_profile_save(profile.user)


@receiver(post_save, sender=FileUpload)
def file_upload_callback(sender, **kwargs):
    file_upload = kwargs['instance']
    MemberAlert.objects.handle_file_upload(file_upload.user)


@receiver(post_save, sender=CoworkingDay)
def coworking_day_callback(sender, **kwargs):
    if getattr(settings, 'SUSPEND_MEMBER_ALERTS', False): return
    coworking_day = kwargs['instance']
    created = kwargs['created']
    if created:
        MemberAlert.objects.handle_sign_in(coworking_day.user)


@receiver(post_save, sender=ResourceSubscription)
def subscription_callback(sender, **kwargs):
    if getattr(settings, 'SUSPEND_MEMBER_ALERTS', False): return
    subscription = kwargs['instance']
    created = kwargs['created']
    updated_fields = kwargs['update_fields']
    ending = updated_fields and 'end_date' in updated_fields and subscription.end_date

    # Who's subscription is this anyway?
    # Sometimes this is None (testing) so we can skip all this madness
    if not subscription.user:
        return
    user = subscription.user

    # Trigger Change Membership
    MemberAlert.objects.handle_change_membership(user)

    # Filter to appropriate trigger depending on resource and if it's new or ending
    if subscription.resource == Resource.objects.desk_resource:
        if created:
            MemberAlert.objects.handle_new_desk(user)
        elif ending and not user.has_desk(subscription.end_date + timedelta(days=1)):
            MemberAlert.objects.handle_ending_desk(user, subscription.end_date)
    elif subscription.resource == Resource.objects.key_resource:
        if created:
            MemberAlert.objects.handle_new_key(user)
        elif ending and subscription.end_date + timedelta(days=1) not in user:
            MemberAlert.objects.handle_ending_key(user, subscription.end_dat)
    elif subscription.resource == Resource.objects.mail_resource:
        if created:
            MemberAlert.objects.handle_new_mail(user)
        elif ending and not user.has_mail(subscription.end_date + timedelta(days=1)):
            MemberAlert.objects.handle_ending_mail(user, subscription.end_dat)

    # If this is a new subscription and they were not an active member
    # the day before this, than this is a new membership!
    if created:
        # TODO - figure out why sometimes start_date comes in as an str
        if type(subscription.start_date) is str:
            subscription.start_date = datetime.strptime(subscription.start_date, '%Y-%m-%d').date()
        the_day_before = subscription.start_date - timedelta(days=1)
        if not user.membership.is_active(the_day_before):
            # Only trigger once even withn multiple subscriptions on one day (Bug #347)
            first_subscription = ResourceSubscription.objects.for_user_and_date(user, subscription.start_date).first()
            if subscription == first_subscription:
                MemberAlert.objects.handle_new_membership(user)


############################################################################
# Models
############################################################################

class MemberAlert(models.Model):
    PAPERWORK = "paperwork"
    MEMBER_INFO = "member_info"
    MEMBER_AGREEMENT = "member_agreement"
    TAKE_PHOTO = "take_photo"
    UPLOAD_PHOTO = "upload_photo"
    POST_PHOTO = "post_photo"
    ORIENTATION = "orientation"
    ONE_MONTH = "one_month"
    KEY_AGREEMENT = "key_agreement"
    STALE_MEMBER = "stale_member"
    #INVALID_BILLING = "invalid_billing"
    ASSIGN_CABINET = "assign_cabinet"
    ASSIGN_MAILBOX = "assign_mailbox"
    REMOVE_PHOTO = "remove_photo"
    REMOVE_SLACK = "remove_slack"
    RETURN_DOOR_KEY = "return_door_key"
    RETURN_DESK_KEY = "return_desk_key"
    REMOVE_MAILBOX = "remove_mailbox"

    ALERT_DESCRIPTIONS = (
        (PAPERWORK, "Received Paperwork"),
        (MEMBER_INFO, "Enter & File Member Information"),
        (MEMBER_AGREEMENT, "Sign Membership Agreement"),
        (TAKE_PHOTO, "Take Photo"),
        (UPLOAD_PHOTO, "Upload Photo"),
        (POST_PHOTO, "Print & Post Photo"),
        (ORIENTATION, "New Member Orientation"),
        (ONE_MONTH, "One Month Check-in"),
        (KEY_AGREEMENT, "Key Training & Agreement"),
        (STALE_MEMBER, "Stale Membership"),
        #(INVALID_BILLING, "Missing Valid Billing"),
        (ASSIGN_CABINET, "Assign a File Cabinet"),
        (ASSIGN_MAILBOX, "Assign a Mailbox"),
        (REMOVE_PHOTO, "Remove Picture from Wall"),
        # (REMOVE_SLACK, "Remove from Slack"),
        (RETURN_DOOR_KEY, "Take Back Keycard"),
        (RETURN_DESK_KEY, "Take Back File Cabinet Key"),
        (REMOVE_MAILBOX, "Remove Mailbox"),
    )

    # These alerts can be resolved by the system automatically
    SYSTEM_ALERTS = [MEMBER_INFO, MEMBER_AGREEMENT, UPLOAD_PHOTO, KEY_AGREEMENT, STALE_MEMBER]

    # These alerts apply to even inactive members
    PERSISTENT_ALERTS = [REMOVE_PHOTO, RETURN_DOOR_KEY, RETURN_DESK_KEY, REMOVE_MAILBOX]

    @staticmethod
    def getDescription(key):
        for k, d in MemberAlert.ALERT_DESCRIPTIONS:
            if k == key:
                return d
        return None

    @staticmethod
    def isSystemAlert(key):
        return key in MemberAlert.SYSTEM_ALERTS

    @staticmethod
    def isPersistantAlert(key):
        return key in MemberAlert.PERSISTENT_ALERTS

    created_ts = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=16)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resolved_ts = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="resolved_alerts", null=True, on_delete=models.CASCADE)
    muted_ts = models.DateTimeField(null=True)
    muted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="muted_alerts", null=True, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_alerts", null=True, on_delete=models.CASCADE)
    note = models.TextField(blank=True, null=True)
    objects = MemberAlertManager()

    def description(self):
        return self.getDescription(self.key)

    def resolve(self, user, note=None):
        self.resolved_ts = localtime(now())
        self.resolved_by = user
        if note:
            self.note = note
        self.save()

    def mute(self, user, note=None):
        self.muted_ts = localtime(now())
        self.muted_by = user
        if note:
            self.note = note
        self.save()

    def is_resolved(self):
        return self.resolved_ts != None or self.is_muted()

    def is_muted(self):
        return self.muted_ts != None

    def is_system_alert(self):
        return self.key in MemberAlert.SYSTEM_ALERTS

    def __str__(self):
        return '%s - %s: %s' % (self.key, self.user, self.is_resolved())

    class Meta:
        app_label = 'nadine'


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
