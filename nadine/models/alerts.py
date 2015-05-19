import logging

from datetime import datetime, time, date, timedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.utils import timezone

from nadine.models.core import Member, Membership, FileUpload
from nadine import mailgun

logger = logging.getLogger(__name__)

# Exiting members is defined by a specific window.  If a new membership
# is added within this window then it is a change not an exit.
# This is the amount of days before and after that create our window.
EXITING_MEMBER_WINDOW = 4

class MemberAlertManager(models.Manager):

    def unresolved(self, key, active_only=True):
        unresolved = self.filter(key=key, resolved_ts__isnull=True, muted_ts__isnull=True)
        # Persistent alerts apply even if a member is inactive
        persistent = key in MemberAlert.PERSISTENT_ALERTS
        if active_only and not persistent:
            active_users = Member.objects.active_users()
            return unresolved.filter(user__in=active_users)
        return unresolved

    def trigger_periodic_check(self):
        # Check for exiting members (3 days back, 3 days forward)
        exiting_members = Member.objects.exiting_members(EXITING_MEMBER_WINDOW)
        for m in exiting_members:
            start = timezone.now() - timedelta(days=EXITING_MEMBER_WINDOW)
            # Only trigger exiting membership if no exit alerts were created in the last week
            if MemberAlert.objects.filter(user=m.user, key__in=MemberAlert.PERSISTENT_ALERTS, created_ts__gte=start).count() == 0:
                self.trigger_exiting_membership(m.user)

        # Check for stale membership
        smd = Member.objects.stale_member_date()
        for m in Member.objects.stale_members():
            existing_alerts = MemberAlert.objects.filter(user=m.user, key=MemberAlert.STALE_MEMBER, created_ts__gte=smd)
            if not existing_alerts:
                MemberAlert.objects.create(user=m.user, key=MemberAlert.STALE_MEMBER)

        # Expire old and unresolved alerts
        #active_users = Member.objects.active_users()
        #exiting_users = exiting_members.values('user')
        # to_clean = [MemberAlert.PAPERWORK, MemberAlert.MEMBER_INFO, MemberAlert.MEMBER_AGREEMENT, MemberAlert.TAKE_PHOTO,
        #	MemberAlert.UPLOAD_PHOTO, MemberAlert.POST_PHOTO, MemberAlert.ORIENTATION, MemberAlert.KEY_AGREEMENT]
        # for key in to_clean:
        #	for alert in self.unresolved(key):
        #		if not alert.user in exiting_users:
        #			if not alert.user in active_users:
        #				alert.mute(None, note="membership ended")

    def trigger_exiting_membership(self, user):
        open_alerts = user.profile.alerts_by_key(include_resolved=False)
        
        # Key?  Let's get it back!
        last_membership = user.profile.last_membership()
        if last_membership:
            if last_membership.has_key:
                if not MemberAlert.RETURN_DOOR_KEY in open_alerts:
                    MemberAlert.objects.create(user=user, key=MemberAlert.RETURN_DOOR_KEY)
            if last_membership.has_desk:
                if not MemberAlert.RETURN_DESK_KEY in open_alerts:
                    MemberAlert.objects.create(user=user, key=MemberAlert.RETURN_DESK_KEY)
            if last_membership.has_mail:
                if MemberAlert.ASSIGN_MAILBOX in open_alerts:
                    # We never assigned a mailbox so we can just resolve that now
                    user.profile.resolve_alerts(MemberAlert.ASSIGN_MAILBOX)
                elif not MemberAlert.REMOVE_MAILBOX in open_alerts:
                    MemberAlert.objects.create(user=user, key=MemberAlert.REMOVE_MAILBOX)
        
        # Take down their photo. 
        if user.profile.photo and not MemberAlert.POST_PHOTO in open_alerts:
            if not MemberAlert.objects.filter(user=user, key=MemberAlert.REMOVE_PHOTO, created_ts__gte=last_membership.start_date):
                MemberAlert.objects.create(user=user, key=MemberAlert.REMOVE_PHOTO)
        
        # Send an email to the team announcing their exit
        mailgun.send_manage_member(user, subject="Exiting Member")


    def trigger_new_membership(self, user):
        logger.debug("trigger_new_membership: %s" % user)

        # Pull a bunch of data so we don't keep hitting the database
        open_alerts = user.profile.alerts_by_key(include_resolved=False)
        all_alerts = user.profile.alerts_by_key(include_resolved=True)
        existing_files = user.profile.files_by_type()
        existing_memberships = user.profile.memberships.all().order_by('start_date')
        new_membership = existing_memberships.last()

        # Member Information
        if not FileUpload.MEMBER_INFO in existing_files:
            if not MemberAlert.PAPERWORK in open_alerts:
                MemberAlert.objects.create(user=user, key=MemberAlert.PAPERWORK)
            if not MemberAlert.PAPERWORK in open_alerts:
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
        if not new_membership.is_change() and not MemberAlert.POST_PHOTO in open_alerts:
            MemberAlert.objects.create(user=user, key=MemberAlert.POST_PHOTO)

        # New Member Orientation
        if not MemberAlert.ORIENTATION in all_alerts:
            MemberAlert.objects.create(user=user, key=MemberAlert.ORIENTATION)

        # Key?  Check for a key agreement
        if new_membership.has_key:
            if not FileUpload.KEY_AGMT in existing_files:
                if not MemberAlert.KEY_AGREEMENT in open_alerts:
                    MemberAlert.objects.create(user=user, key=MemberAlert.KEY_AGREEMENT)

        # Assign a mailbox if this membership comes with mail
        if new_membership.has_mail:
            if MemberAlert.REMOVE_MAILBOX in open_alerts:
                # No need to remove the mailbox since their new membership has mail
                user.profile.resolve_alerts(MemberAlert.REMOVE_MAILBOX)
            else:
                if not MemberAlert.ASSIGN_MAILBOX in open_alerts:
                    MemberAlert.objects.create(user=user, key=MemberAlert.ASSIGN_MAILBOX)

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
        user.profile.resolve_alerts(MemberAlert.STALE_MEMBER)


class MemberAlert(models.Model):
    PAPERWORK = "paperwork"
    MEMBER_INFO = "member_info"
    MEMBER_AGREEMENT = "member_agreement"
    TAKE_PHOTO = "take_photo"
    UPLOAD_PHOTO = "upload_hoto"
    POST_PHOTO = "post_photo"
    ORIENTATION = "orientation"
    KEY_AGREEMENT = "key_agreement"
    STALE_MEMBER = "stale_member"
    #INVALID_BILLING = "invalid_billing"
    ASSIGN_MAILBOX = "assign_mailbox"
    REMOVE_PHOTO = "remove_photo"
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
        (KEY_AGREEMENT, "Key Training & Agreement"),
        (STALE_MEMBER, "Stale Membership"),
        #(INVALID_BILLING, "Missing Valid Billing"),
        (ASSIGN_MAILBOX, "Assign a Mailbox"),
        (REMOVE_PHOTO, "Remove Picture from Wall"),
        (RETURN_DOOR_KEY, "Take Back Keycard"),
        (RETURN_DESK_KEY, "Take Back Roller Drawer Key"),
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

    created_ts = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=16)
    user = models.ForeignKey(User)
    resolved_ts = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey(User, related_name="resolved_by", null=True)
    muted_ts = models.DateTimeField(null=True)
    muted_by = models.ForeignKey(User, related_name="muted_by", null=True)
    note = models.TextField(blank=True, null=True)
    objects = MemberAlertManager()

    def description(self):
        for k, d in MemberAlert.ALERT_DESCRIPTIONS:
            if self.key == k:
                return d
        return None

    def resolve(self, user, note=None):
        self.resolved_ts = timezone.now()
        self.resolved_by = user
        if note:
            self.note = note
        self.save()

    def mute(self, user, note=None):
        self.muted_ts = timezone.now()
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

    def __unicode__(self):
        return '%s - %s: %s' % (self.key, self.user, self.is_resolved())

    class Meta:
        app_label = 'nadine'


def membership_callback(sender, **kwargs):
    print ("membership_callback")
    membership = kwargs['instance']
    created = kwargs['created']
    if created:
        MemberAlert.objects.trigger_new_membership(membership.member.user)
    else:
        # If this membership has an end date that puts it outside our exiting membership window
        # we are going to go straight to the exiting member logic from here
        window_start = timezone.now() - timedelta(days=EXITING_MEMBER_WINDOW)
        if membership.end_date and membership.end_date < window_start.date():
            MemberAlert.objects.trigger_exiting_membership(membership.member.user)
post_save.connect(membership_callback, sender=Membership)
