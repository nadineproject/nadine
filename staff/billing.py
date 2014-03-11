import time
import logging
import settings
import traceback
from models import Bill, BillingLog, Transaction, Member, Membership, DailyLog
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import datetime, timedelta, date

logger = logging.getLogger(__name__)

class Day:
	"""All of the daily_logs, memberships, and (optionally) a bill associated with this day of a Run."""
	def __init__(self, date):
		self.date = date
		self.membership = None
		self.daily_log = None
		self.guest_daily_logs = []
		self.bill = None

	def is_membership_end_date(self): return self.membership and self.membership.end_date and self.membership.end_date == self.date

	def is_membership_anniversary(self): return self.membership and self.membership.is_anniversary_day(self.date)

	def __repr__(self):
		return 'Day %s' % self.date

class Run:
	"""The information which is gathered for a time period in order to calculate billing."""
	def __init__(self, member, start_date, end_date, filter_closed_logs=True):
		#logger.debug(("Run: member=%s, start=%s, end=%s") % (member, start_date, end_date))

		self.member = member
		self.start_date = start_date
		self.end_date = end_date
		self.days = []
		self.filter_closed_logs = filter_closed_logs
		
		
		self.populate_days()
		self.populate_memberships()
		self.populate_daily_logs()

	def non_member_daily_logs(self):
		"""Returns a tuple (daily_logs, guest_daily_logs) [each sorted ascending by date] in this run which are not covered by a membership, including guest daily logs"""
		reversed_days = [day for day in self.days]
		reversed_days.reverse()
		daily_logs = []
		guest_daily_logs = []
		for day in reversed_days:
			if day.membership: break # assume that this and the days before this are covered by the membership
			if day.daily_log != None: daily_logs.append(day.daily_log)
			for gdl in day.guest_daily_logs: guest_daily_logs.append(gdl)
				
		daily_logs.reverse()
		guest_daily_logs.reverse()
		return (daily_logs, guest_daily_logs)
	
	def has_guest_daily_logs(self):
		for day in self.days:
			if len(day.guest_daily_logs) > 0: return True
		return False

	def populate_days(self):
		for i in range((self.end_date - self.start_date).days + 1):
			self.days.append(Day(self.start_date + timedelta(days=i)))

	def populate_memberships(self):
		for membership in Membership.objects.filter(member=self.member).order_by('start_date'):
			if membership.end_date and membership.end_date < self.start_date: continue
			if membership.start_date > self.end_date: continue
			for i in range(0, len(self.days)):
				if self.days[i].date >= membership.start_date:
					if membership.end_date == None or self.days[i].date <= membership.end_date:
						if self.days[i].membership: print 'Duplicate membership! %s' % membership
						self.days[i].membership = membership

	def populate_daily_logs(self):
		# Grab all the daily_logs from this member
		daily_logs = DailyLog.objects.filter(member=self.member, payment="Bill", guest_of=None).filter(visit_date__gte=self.start_date).filter(visit_date__lte=self.end_date)
		if self.filter_closed_logs: daily_logs = daily_logs.annotate(bill_count=Count('bills')).filter(bill_count=0)
		for log in daily_logs.order_by('visit_date'):
			self.add_daily_log(log)

		# Grab all the daily_logs marked as a guest of this member
		daily_logs = DailyLog.objects.filter(guest_of=self.member, payment="Bill").filter(visit_date__gte=self.start_date).filter(visit_date__lte=self.end_date)
		if self.filter_closed_logs: daily_logs = daily_logs.annotate(bill_count=Count('bills')).filter(bill_count=0)
		for log in daily_logs.order_by('visit_date'):
			self.add_guest_log(log)

		# Grab all the daily_logs attached to memberships marked as guests of this member
		for membership in Membership.objects.filter(guest_of=self.member).order_by('start_date'):
			if membership.end_date and membership.end_date < self.start_date: continue
			if membership.start_date > self.end_date: continue
			for log in DailyLog.objects.filter(member=membership.member, payment="Bill", guest_of=None).filter(visit_date__gte=self.start_date).filter(visit_date__lte=self.end_date):
				self.add_guest_log(log)

	def add_daily_log(self, log):
		for i in range(0, len(self.days)):
			if log.visit_date == self.days[i].date:
				if self.days[i].membership and self.days[i].membership.guest_of:
					# Skip guest activity.  It will get picked up by the host's bill.
					break
				self.days[i].daily_log = log
				break

	def add_guest_log(self, log):
		for i in range(0, len(self.days)):
			if log.visit_date == self.days[i].date:
				self.days[i].guest_daily_logs.append(log)
				break

	def print_info(self):
		for day in self.days:
			if day.daily_log or day.is_membership_end_date() or day.is_membership_anniversary() or len(day.guest_daily_logs) > 0:
				if day.daily_log: print '\tDaily log: %s' % day.daily_log.visit_date
				if day.is_membership_end_date(): print '\t%s end: %s' % (day.membership.membership_plan, day.date)
				if day.is_membership_anniversary(): print '\t%s monthly anniversary: %s' % (day.membership.membership_plan, day.date)
				if len(day.guest_daily_logs) > 0: print '\tGuest logs: %s' % day.guest_daily_logs

	def __repr__(self):
		if len(self.days) == 0: return 'Run for %s' % self.member
		return 'Run for %s (%s / %s)' % (self.member, self.days[0].date, self.days[len(self.days) - 1].date)

def run_billing(bill_time=timezone.localtime(timezone.now())):
	"""Generate billing records for every member who deserves it."""
	bill_date = datetime.date(bill_time)
	logger.info("run_billing: bill_time=%s, bill_date=%s" % (bill_time, bill_date))
	try:
		latest_billing_log = BillingLog.objects.latest()
	except ObjectDoesNotExist:
		latest_billing_log = None
	if latest_billing_log and not latest_billing_log.ended:
		logger.warning("run_billing:The last billing log (%s) claims to be in progress.	Aborting billing." % latest_billing_log)
		return

	billing_log = BillingLog.objects.create()
	billing_success = False
	bill_count = 0
	try:
			# This should be changed to "all members w/ activity or an active membership"
			for member in Member.objects.all():
				last_bill = member.last_bill()
				if last_bill:
					start_date = last_bill.created + timedelta(days=1)
				else:
					start_date = bill_date - timedelta(days=62)
					if start_date < settings.BILLING_START_DATE: start_date = settings.BILLING_START_DATE
				run = Run(member, start_date, bill_date)
				for day_index in range(0, len(run.days)): # look for days on which we should bill for a membership
					day = run.days[day_index]
					if day.is_membership_anniversary() or day.is_membership_end_date(): # calculate a member bill
						bill_dropins = []
						bill_guest_dropins = []
						recent_days = run.days[0:day_index + 1]
						recent_days.reverse()
						for recent_day in recent_days: # gather the daily logs for this member and guests under this membership
							if recent_day.bill:
								break
							if recent_day.daily_log: bill_dropins.append(recent_day.daily_log)
							for guest_daily_log in recent_day.guest_daily_logs: bill_guest_dropins.append(guest_daily_log)
						# now calculate the bill amount
						bill_amount = 0
						monthly_fee = day.membership.monthly_rate
						if day.is_membership_end_date(): monthly_fee = 0
						billable_dropin_count = max(0, len(bill_dropins) + len(bill_guest_dropins) - day.membership.dropin_allowance)
						bill_amount = monthly_fee + (billable_dropin_count * day.membership.daily_rate)
						day.bill = Bill(created=day.date, amount=bill_amount, member=member, paid_by=day.membership.guest_of, membership=day.membership)
						logger.debug('saving bill: %s - %s - %s' % (day.bill, day, billable_dropin_count))
						day.bill.save()
						bill_count += 1
						day.bill.dropins = [dropin.id for dropin in bill_dropins]
						day.bill.guest_dropins = [dropin.id for dropin in bill_guest_dropins]
						day.bill.save()

						# Close out the transaction if no money is due
						if bill_amount == 0:
							transaction = Transaction(member=member, amount=0, status='closed')
							transaction.save()
							transaction.bills = [day.bill]
							transaction.save()

				# Now calculate a bill for non-member drop-ins if they exist and it has been two weeks since we billed them
				bill_dropins, guest_bill_dropins = run.non_member_daily_logs()
				if len(bill_dropins) > 0 or len(guest_bill_dropins) > 0:
					time_to_bill_guests = len(guest_bill_dropins) > 0 and (bill_date - guest_bill_dropins[0].visit_date) >= timedelta(weeks=2)
					time_to_bill_dropins = len(bill_dropins) > 0 and (bill_date - bill_dropins[0].visit_date) >= timedelta(weeks=2)
					if time_to_bill_guests or time_to_bill_dropins:
						bill_amount = (len(bill_dropins) + len(guest_bill_dropins)) * settings.NON_MEMBER_DROPIN_FEE
						last_day = run.days[len(run.days) - 1]
						last_day.bill = Bill(created=last_day.date, amount=bill_amount, member=member)
						last_day.bill.save()
						bill_count += 1
						last_day.bill.dropins = [dropin.id for dropin in bill_dropins]
						last_day.bill.guest_dropins = [dropin.id for dropin in guest_bill_dropins]
						last_day.bill.save()

			billing_success = True
			logger.info("run_billing: Successfully created %s bills" % bill_count)
	except:
		billing_log.note = traceback.format_exc()
	finally:
		billing_log.ended = timezone.localtime(timezone.now())
		billing_log.successful = billing_success
		billing_log.save()
		logger.info("run_billing: Done! Success=%s" % billing_success)
		if not billing_success: 
			logger.error(billing_log.note)

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
