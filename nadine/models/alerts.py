

import logging

from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.timezone import localtime, now

from nadine.models.profile import UserProfile, FileUpload
from nadine.models.membership import Membership, IndividualMembership, ResourceSubscription
from nadine.models.usage import CoworkingDay
from nadine.models.resource import Resource
from interlink.models import MailingList

from nadine import email
from nadine.utils.slack_api import SlackAPI
from nadine.utils.payment_api import PaymentAPI

logger = logging.getLogger(__name__)


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
    # Trigger Actions
    #######################################################################

    def trigger_periodic_check(self):
        logger.debug("trigger_periodic_check")

        # Check for exiting members in the coming week
        exit_date = localtime(now()) + timedelta(days=5)
        exiting_members = User.helper.exiting_members(exit_date)
        for u in exiting_members:
            # Only trigger exiting membership if no exit alerts were created in the last week
            start = localtime(now()) - timedelta(days=5)
            if MemberAlert.objects.filter(user=u, key__in=MemberAlert.PERSISTENT_ALERTS, created_ts__gte=start).count() == 0:
                self.trigger_ending_membership(u, exit_date)

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

    def trigger_change_subscription(self, user):
        # Turn off automatic billing
        payment_api = PaymentAPI()
        if payment_api.enabled:
            payment_api.disable_recurring(user.username)

    def trigger_ending_membership(self, user, target_date=None):
        logger.debug("trigger_ending_membership: %s, %s" % (user, target_date))
        if target_date == None:
            target_date = localtime(now())

        # If they have a photo, take it down and stop nagging us to take one
        if user.profile.photo:
            user.profile.resolve_alerts(MemberAlert.POST_PHOTO)
            MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.REMOVE_PHOTO)

        # Send an email to the team announcing their exit
        end = user.membership.end_date
        subject = "Exiting Member: %s/%s/%s" % (end.month, end.day, end.year)
        email.send_manage_member(user, subject=subject)

        # Remove them from the mailing lists
        for mailing_list in MailingList.objects.filter(is_opt_out=True):
            mailing_list.subscribers.remove(user)

    def trigger_new_membership(self, user):
        logger.debug("trigger_new_membership: %s" % user)

        # Pull a bunch of data so we don't keep hitting the database
        open_alerts = user.profile.alerts_by_key(include_resolved=False)
        all_alerts = user.profile.alerts_by_key(include_resolved=True)
        existing_files = user.profile.files_by_type()

        # Send New Member email
        try:
            email.send_new_membership(user)
            email.announce_new_membership(user)
        except Exception as e:
            logger.error("Could not send New Member notification", e)

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

        # Subscribe them to all the opt_out mailing lists
        for mailing_list in MailingList.objects.filter(is_opt_out=True):
            mailing_list.subscribers.add(user)

        # Invite them to slack
        if hasattr(settings, 'SLACK_API_TOKEN'):
            SlackAPI().invite_user_quiet(user)

    def trigger_profile_save(self, profile):
        logger.debug("trigger_profile_save: %s" % profile)
        if profile.photo:
            profile.resolve_alerts(MemberAlert.TAKE_PHOTO)
            profile.resolve_alerts(MemberAlert.UPLOAD_PHOTO)

    def trigger_file_upload(self, user):
        logger.debug("trigger_file_upload: %s" % user)
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

    def trigger_sign_in(self, user):
        logger.debug("trigger_sign_in: %s" % user)

        # If they have signed in, they are not stale anymore
        user.profile.resolve_alerts(MemberAlert.STALE_MEMBER)

        # Send out a bunch of things the first time they sign in
        if CoworkingDay.objects.filter(user=user).count() == 1:
            try:
                email.announce_free_trial(user)
                email.send_introduction(user)
                email.subscribe_to_newsletter(user)
            except:
                logger.error("Could not send introduction email to %s" % user.email)
        else:
            # If it's not their first day and they still have open alerts, message the team
            if len(user.profile.open_alerts()) > 0:
                email.send_manage_member(user)

    def trigger_new_desk(self, user):
        logger.debug("trigger_new_desk: %s" % user)
        # No need to return the desk key since their new membership has a desk
        user.profile.resolve_alerts(MemberAlert.RETURN_DESK_KEY)
        # A desk comes with a cabinet
        MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.ASSIGN_CABINET)

    def trigger_ending_desk(self, user, end_date):
        logger.debug("trigger_ending_desk: %s" % user)
        user.profile.resolve_alerts(MemberAlert.ASSIGN_CABINET)
        MemberAlert.objects.create_if_new(user=user, key=MemberAlert.RETURN_DESK_KEY)

    def trigger_new_key(self, user):
        logger.debug("trigger_new_key: %s" % user)
        # No need to return the door key if they now have a key
        user.profile.resolve_alerts(MemberAlert.RETURN_DOOR_KEY)
        # Check for a key agreement
        if not FileUpload.KEY_AGMT in user.profile.files_by_type():
            MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.KEY_AGREEMENT)

    def trigger_ending_key(self, user, end_date):
        logger.debug("trigger_ending_key: %s" % user)
        # They need to return their door key
        MemberAlert.objects.create_if_new(user, MemberAlert.RETURN_DOOR_KEY, end_date)

    def trigger_new_mail(self, user):
        logger.debug("trigger_new_mail: %s" % user)
        # No need to remove the mailbox since their new membership has mail
        user.profile.resolve_alerts(MemberAlert.REMOVE_MAILBOX)
        # Assign a mailbox
        MemberAlert.objects.create_if_not_open(user=user, key=MemberAlert.ASSIGN_MAILBOX)

    def trigger_ending_mail(self, user, end_date):
        logger.debug("trigger_ending_mail: %s" % user)
        # We don't need to assign a mailbox if they are ending it
        user.profile.resolve_alerts(MemberAlert.ASSIGN_MAILBOX)
        MemberAlert.objects.create_if_new(user=user, key=MemberAlert.REMOVE_MAILBOX)


############################################################################
# Call Backs
############################################################################


@receiver(post_save, sender=CoworkingDay)
def coworking_day_callback(sender, **kwargs):
    if getattr(settings, 'SUSPEND_MEMBER_ALERTS', False): return
    coworking_day = kwargs['instance']
    created = kwargs['created']
    if created:
        MemberAlert.objects.trigger_sign_in(coworking_day.user)


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

    # Trigger Change Subscription
    MemberAlert.objects.trigger_change_subscription(user)

    # Filter to appropriate trigger depending on resource and if it's new or ending
    if subscription.resource == Resource.objects.desk_resource:
        if created:
            MemberAlert.objects.trigger_new_desk(user)
        elif ending and not user.has_desk(subscription.end_date + timedelta(days=1)):
            MemberAlert.objects.trigger_ending_desk(user, subscription.end_date)
    elif subscription.resource == Resource.objects.key_resource:
        if created:
            MemberAlert.objects.trigger_new_key(user)
        elif ending and subscription.end_date + timedelta(days=1) not in user:
            MemberAlert.objects.trigger_ending_key(user, subscription.end_dat)
    elif subscription.resource == Resource.objects.mail_resource:
        if created:
            MemberAlert.objects.trigger_new_mail(user)
        elif ending and not user.has_mail(subscription.end_date + timedelta(days=1)):
            MemberAlert.objects.trigger_ending_mail(user, subscription.end_dat)

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
                MemberAlert.objects.trigger_new_membership(user)

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


# Copyright 2019 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
