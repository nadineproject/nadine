from django.db import models
from django.db.models import Q

from staff.models.core import *

class MembershipPlan(models.Model):
	"""Options for monthly membership"""
	name = models.CharField(max_length=16)
	description = models.CharField(max_length=128, blank=True, null=True)
	monthly_rate = models.IntegerField(default=0)
	daily_rate = models.IntegerField(default=0)
	dropin_allowance = models.IntegerField(default=0)
	has_desk = models.NullBooleanField(default=False)

	def __str__(self): return self.name

	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_membershipplan_change', args=[self.id])

	class Meta:
		app_label = 'staff'
		verbose_name = "Membership Plan"
		verbose_name_plural = "Membership Plans"

class MembershipManager(models.Manager):

	def by_date(self, target_date):
		return self.filter(start_date__lte=target_date).filter(Q(end_date__isnull=True) | Q(end_date__gte=target_date))

	def create_with_plan(self, member, start_date, end_date, membership_plan, rate=-1, guest_of=None):
		if rate < 0:
			rate = membership_plan.monthly_rate 
		self.create(member=member, start_date=start_date, end_date=end_date, membership_plan=membership_plan,
			monthly_rate=rate, daily_rate=membership_plan.daily_rate, dropin_allowance=membership_plan.dropin_allowance,
			has_desk=membership_plan.has_desk, guest_of=guest_of)

		class Meta:
			app_label = 'staff'

class Membership(models.Model):
	"""A membership level which is billed monthly"""
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
		if Membership.objects.by_date(self.start_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
			raise Exception('Already have a Membership for that start date')
		if self.end_date and Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
			raise Exception('Already have a Membership for that end date: %s' % Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member))
		if self.end_date and self.start_date > self.end_date:
			raise Exception('A Membership cannot start after it ends')
		super(Membership, self).save(*args, **kwargs)

	def is_active(self, on_date=None):
		if not on_date:
			on_date = date.today()
		if self.start_date > on_date: return False
		return self.end_date == None or self.end_date >= on_date

	def is_anniversary_day(self, test_date):
		# Do something smarter if we're at the end of February
		if test_date.month == 2 and test_date.day == 28:
			if self.start_date.day >= 29: return True

		# 30 days has September, April, June, and November
		if self.start_date.day == 31 and test_date.day == 30:
			if test_date.month in [9, 4, 6, 11]: return True
		return test_date.day == self.start_date.day

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
		return urlresolvers.reverse('admin:staff_membership_change', args=[self.id])

	class Meta:
		app_label = 'staff'
		verbose_name = "Membership"
		verbose_name_plural = "Memberships"
		ordering = ['start_date'];