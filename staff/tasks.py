from celery.task import task
from datetime import datetime, timedelta
from models import Member, Membership, DailyLog, BillingLog
from members.models import UserNotification
from django.utils import timezone
from arpwatch import arp
import billing
import email

@task()
def billing_task():
	"""A recurring task which calculates billing"""
	billing.run_billing()

@task()
def first_day_checkins():
	"""A recurring task which sends an email to new members"""
	now = timezone.now()
	midnight = now - timedelta(seconds=now.hour*60*60 + now.minute*60 + now.second)
	free_trials = DailyLog.objects.filter(visit_date__range=(midnight, now), payment='Trial')
	for l in free_trials:
		email.send_first_day_checkin(l.member.user)

@task()
def regular_checkins():
	"""A recurring task which sends checkin emails to members"""
	# Pull the memberships that started 60 days ago and send the coworking survey
	# if they are still active and this was their first membership
	two_months_ago = timezone.now() - timedelta(days=60)
	for membership in Membership.objects.filter(start_date=two_months_ago):
		if Membership.objects.filter(member=membership.member, start_date__lt=two_months_ago).count() == 0:
			if membership.member.is_active():
				email.send_member_survey(membership.member.user)
				
	# Pull all the free trials from 30 days ago and send an email if they haven't been back
	one_month_ago = timezone.now() - timedelta(days=30)
	for dropin in DailyLog.objects.filter(visit_date=one_month_ago, payment='Trial'):
		if DailyLog.objects.filter(member=dropin.member).count() == 1:
			if not dropin.member.is_active():
				email.send_no_return_checkin(dropin.member.user)

	# Send an exit survey to members that have been gone a week.
	one_week_ago = timezone.now() - timedelta(days=7)
	for membership in Membership.objects.filter(end_date=one_week_ago):
		if not membership.member.is_active():
			email.send_exit_survey(membership.member.user)

	# Announce to the team when a new user is nearing the end of their first month
	almost_a_month_ago = timezone.now() - timedelta(days=21)
	for membership in Membership.objects.filter(start_date=almost_a_month_ago):
		if Membership.objects.filter(member=membership.member, start_date__lt=almost_a_month_ago).count() == 0:
			if membership.member.is_active():
				email.announce_member_checkin(membership.member.user)
@task()
def unsubscribe_recent_dropouts_task():
	"""A recurring task which checks for members who need to be unsubscribed from mailing lists"""
	from models import Member
	Member.objects.unsubscribe_recent_dropouts()

@task()
def make_backup():
	from staff.backup import BackupManager
	manager = BackupManager()
	manager.make_backup()
	
@task()
def send_notifications():
	here_today = arp.here_today()
	for n in UserNotification.objects.filter(sent_date__isnull=True):
		if n.notify_user.get_profile() in here_today:
			if n.target_user.get_profile() in here_today:
				email.send_user_notifications(n.notify_user, n.target_user)
				n.sent_date=timezone.now()
				n.save()

# Copyright 2012 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
