from __future__ import absolute_import

from celery import shared_task
from datetime import datetime, timedelta

from django.utils import timezone

from nadine.models.core import Member, Membership, DailyLog
from nadine.models.payment import BillingLog
from members.models import UserNotification

from arpwatch import arp
from staff import email, billing


@shared_task
def billing_task():
    """A recurring task which calculates billing"""
    billing.run_billing()


@shared_task
def first_day_checkins():
    """A recurring task which sends an email to new members"""
    now = timezone.localtime(timezone.now())
    midnight = now - timedelta(seconds=now.hour * 60 * 60 + now.minute * 60 + now.second)
    free_trials = DailyLog.objects.filter(visit_date__range=(midnight, now), payment='Trial')
    for l in free_trials:
        email.send_first_day_checkin(l.user)


@shared_task
def regular_checkins():
    """A recurring task which sends checkin emails to members"""
    # Pull the memberships that started 60 days ago and send the coworking survey
    # if they are still active and this was their first membership
    two_months_ago = timezone.localtime(timezone.now()) - timedelta(days=60)
    for membership in Membership.objects.filter(start_date=two_months_ago):
        if Membership.objects.filter(user=membership.user, start_date__lt=two_months_ago).count() == 0:
            if membership.user.profile.is_active():
                email.send_member_survey(membership.user)

    # Pull all the free trials from 30 days ago and send an email if they haven't been back
    one_month_ago = timezone.localtime(timezone.now()) - timedelta(days=30)
    for dropin in DailyLog.objects.filter(visit_date=one_month_ago, payment='Trial'):
        if DailyLog.objects.filter(user=dropin.user).count() == 1:
            if not dropin.user.profile.is_active():
                email.send_no_return_checkin(dropin.user)

    # Send an exit survey to members that have been gone a week.
    one_week_ago = timezone.localtime(timezone.now()) - timedelta(days=7)
    for membership in Membership.objects.filter(end_date=one_week_ago):
        if not membership.user.profile.is_active():
            email.send_exit_survey(membership.user)

    # Announce to the team when a new user is nearing the end of their first month
    #almost_a_month_ago = timezone.localtime(timezone.now()) - timedelta(days=21)
    # for membership in Membership.objects.filter(start_date=almost_a_month_ago):
    #	if Membership.objects.filter(user=membership.user, start_date__lt=almost_a_month_ago).count() == 0:
    #		if membership.user.profile.is_active():
    #			email.announce_member_checkin(membership.user)


@shared_task
def member_alert_check():
    from nadine.models.alerts import MemberAlert
    MemberAlert.objects.trigger_periodic_check()


@shared_task
def unsubscribe_recent_dropouts_task():
    """A recurring task which checks for members who need to be unsubscribed from mailing lists"""
    from nadine.models.core import Member
    Member.objects.unsubscribe_recent_dropouts()


@shared_task
def make_backup():
    from staff.backup import BackupManager
    manager = BackupManager()
    manager.make_backup()


@shared_task
def export_active_users():
    from staff.backup import BackupManager
    manager = BackupManager()
    manager.export_active_users()


@shared_task
def anniversary_checkin():
    from nadine.models.core import Member
    for m in Member.objects.active_members():
        d = m.duration()
        if d.years and not d.months and not d.days:
            email.announce_anniversary(m.user)
            email.send_edit_profile(m.user)


@shared_task
def announce_special_days():
    from nadine.models.core import Member
    for m in Member.objects.active_members():
        for sd in SpecialDay.objects.filter(member=m):
            if sd.month == today.month and sd.day == today.day:
                email.announce_special_day(m.user, sd)


@shared_task
def send_notifications():
    here_today = Member.objects.here_today()
    for n in UserNotification.objects.filter(sent_date__isnull=True):
        if n.notify_user.get_profile() in here_today:
            if n.target_user.get_profile() in here_today:
                email.send_user_notifications(n.notify_user, n.target_user)
                n.sent_date = timezone.localtime(timezone.now())
                n.save()

# Copyright 2012 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
