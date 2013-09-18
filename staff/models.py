import pprint, traceback
from datetime import datetime, time, date, timedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.encoding import smart_str, smart_unicode
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils import timezone

from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_localflavor_us\.models\.USStateField"])
add_introspection_rules([], ["^django_localflavor_us\.models\.PhoneNumberField"])

GENDER_CHOICES = (
	('U', 'Unknown'),
	('M', 'Male'),
	('F', 'Female'),
	('O', 'Other'),
)

PAYMENT_CHOICES = (
	('Bill', 'Billable'),
	('Trial', 'Free Trial'),
	('Waved', 'Payment Waved'),
)

class BillingLog(models.Model):
	"""A record of when the billing was last calculated and whether it was successful"""
	started = models.DateTimeField(auto_now_add=True)
	ended = models.DateTimeField(blank=True, null=True)
	successful = models.BooleanField(default=False)
	note = models.TextField(blank=True, null=True)
	class Meta:
	   ordering = ['-started']
	   get_latest_by = 'started'
	def __unicode__(self):
	   return 'BillingLog %s: %s' % (self.started, self.successful)
	def ended_date(self):
	   if not self.ended: return None
	   return datetime.date(self.ended)

class Bill(models.Model):
	"""A record of what fees a Member owes."""
	member = models.ForeignKey('Member', blank=False, null=False, related_name="bills")
	amount = models.DecimalField(max_digits=7, decimal_places=2)
	created = models.DateField(blank=False, null=False)
	membership = models.ForeignKey('Membership', blank=True, null=True)
	dropins = models.ManyToManyField('DailyLog', blank=True, null=True, related_name='bills')
	guest_dropins = models.ManyToManyField('DailyLog', blank=True, null=True, related_name='guest_bills')
	new_member_deposit = models.BooleanField(default=False, blank=False, null=False)
	paid_by = models.ForeignKey('Member', blank=True, null=True, related_name='guest_bills')

	class Meta:
		ordering= ['-created']
		get_latest_by = 'created'
	def __unicode__(self):
		return 'Bill %s: %s %s' % (self.id, self.member, self.amount)
	@models.permalink
	def get_absolute_url(self):
		return ('staff.views.bill', (), { 'id':self.id })
	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_bill_change', args=[self.id])

class Transaction(models.Model):
	"""A record of charges for a member."""
	created = models.DateTimeField(auto_now_add=True)
	member = models.ForeignKey('Member', blank=False, null=False)
	TRANSACTION_STATUS_CHOICES = ( ('open', 'Open'), ('closed', 'Closed') )
	status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, blank=False, null=False, default='open')
	bills = models.ManyToManyField(Bill, blank=False, null=False, related_name='transactions')
	amount = models.DecimalField(max_digits=7, decimal_places=2)
	note = models.TextField(blank=True, null=True)
	class Meta:
		ordering= ['-created']
	def __unicode__(self):
		return '%s: %s' % (self.member.full_name, self.amount)
	@models.permalink
	def get_absolute_url(self):
		return ('staff.views.transaction', (), { 'id':self.id })
	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_transaction_change', args=[self.id])

class HowHeard(models.Model):
	"""A record of how a member discovered the space"""
	name = models.CharField(max_length=128)
	def __str__(self): return self.name
	class Meta:
		ordering = ['name']

class Industry(models.Model):
	"""The type of work a member does"""
	name = models.CharField(max_length=128)
	def __str__(self): return self.name
	class Meta:
		verbose_name = "Industry"
		verbose_name_plural = "Industries"
		ordering = ['name']

class Neighborhood(models.Model):
	name = models.CharField(max_length=128)
	def __str__(self): return self.name
	class Meta:
		ordering = ['name']

class MemberManager(models.Manager):
	def member_count(self, active_only):
		if active_only:
			return Member.objects.filter(memberships__start_date__isnull=False, memberships__end_date__isnull=True).count();
		else:
			return Member.objects.all().count()

	def active_members(self):
		unending = Q(memberships__end_date__isnull=True)
		future_ending = Q(memberships__end_date__gt=timezone.now().date())
		return Member.objects.exclude(memberships__isnull=True).filter(unending | future_ending).distinct()

	def daily_members(self):
		member_list = []
		for active_member in self.active_members().order_by('user__first_name'):
			if not active_member.last_membership().has_desk:
				member_list.append(active_member)
		return member_list

	def invalid_billing(self):
		members = []
		for m in self.active_members():
			if not m.has_valid_billing():
				members.append(m)
		return members
		
	def recent_members(self, days):
		return Member.objects.filter(user__date_joined__gt=timezone.localtime(timezone.now())- timedelta(days=days))
		
	def members_by_plan_id(self, plan_id):
		return [m.member for m in Membership.objects.filter(membership_plan=plan_id).filter(Q(end_date__isnull=True, start_date__lte=timezone.now().date()) | Q(end_date__gt=timezone.now().date())).distinct().order_by('member__user__first_name')]

	def members_by_neighborhood(self, hood, active_only=True):
		if active_only:
			return Member.objects.filter(neighborhood=hood).filter(memberships__isnull=False).filter(Q(memberships__end_date__isnull=True) | Q(memberships__end_date__gt=timezone.now().date())).distinct()
		else:
			return Member.objects.filter(neighborhood=hood)

	def unsubscribe_recent_dropouts(self):
		"""Remove mailing list subscriptions from members whose memberships expired yesterday and they do not start a membership today"""
		from interlink.models import MailingList
		recently_expired = Member.objects.filter(memberships__end_date=timezone.now().date() - timedelta(days=1)).exclude(memberships__start_date=timezone.now().date())
		for member in recently_expired:
			MailingList.objects.unsubscribe_from_all(member.user)

	def search(self, search_string, active_only=False):
		terms = search_string.split()
		if len(terms) == 0: return None;
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

class Member(models.Model):
	"""A person who has used the space and may or may not have a monthly membership"""
	objects = MemberManager()

	user = models.ForeignKey(User, unique=True, blank=False, related_name="user")
	email2 = models.EmailField("Alternate Email", blank=True, null=True)
	phone = PhoneNumberField(blank=True, null=True)
	phone2 = PhoneNumberField("Alternate Phone", blank=True, null=True)
	address1 = models.CharField(max_length = 128, blank = True)
	address2 = models.CharField(max_length = 128, blank = True)
	city = models.CharField(max_length = 128, blank = True)
	state = models.CharField(max_length = 2, blank = True)
	zipcode = models.CharField(max_length = 5, blank = True)
	url_personal = models.URLField(blank=True, null=True)
	url_professional = models.URLField(blank=True, null=True)
	url_facebook = models.URLField(blank=True, null=True)
	url_twitter = models.URLField(blank=True, null=True)
	url_biznik = models.URLField(blank=True, null=True)
	url_linkedin = models.URLField(blank=True, null=True)
	url_aboutme = models.URLField(blank=True, null=True)
	url_github = models.URLField(blank=True, null=True)
	gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="U")
	howHeard = models.ForeignKey(HowHeard, blank=True, null=True)
	#referred_by = models.ForeignKey(User, verbose_name="Referred By", related_name="referred_by", blank=True, null=True)
	industry = models.ForeignKey(Industry, blank=True, null=True)
	neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True)
	has_kids = models.NullBooleanField(blank=True, null=True)
	self_employed = models.NullBooleanField(blank=True, null=True)
	company_name = models.CharField(max_length=128, blank=True, null=True)
	promised_followup = models.DateField(blank=True, null=True)
	last_modified = models.DateField(auto_now=True, editable=False)
	notes = models.TextField(blank=True, null=True)
	photo = models.ImageField(upload_to='member_photo', blank=True, null=True)
	tags = TaggableManager(blank=True)
	valid_billing = models.BooleanField(default=False)

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
		return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).order_by('-created')

	def open_bills(self):
		"""Returns all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
		return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).filter(transactions=None).order_by('created')

	def open_bills_amount(self):
		"""Returns the amount of all of the open bills, both for this member and any bills for other members which are marked to be paid by this member."""
		return Bill.objects.filter(models.Q(member=self) | models.Q(paid_by=self)).filter(transactions=None).aggregate(models.Sum('amount'))['amount__sum']

	def pay_bills_form(self):
		from forms import PayBillsForm
		return PayBillsForm(initial={'member_id':self.id, 'amount':self.open_bills_amount })

	def last_bill(self):
		"""Returns the latest Bill, or None if the member has not been billed.
		NOTE: This does not (and should not) return bills which are for other members but which are to be paid by this member."""
		bills = Bill.objects.filter(member=self)
		if len(bills) == 0: return None
		return bills[0]

	def last_membership(self):
		"""Returns the latest membership, even if it has an end date, or None if none exists"""
		memberships = Membership.objects.filter(member=self).order_by('-start_date', 'end_date')[0:]
		if memberships == None or len(memberships) == 0: return None
		return memberships[0]

	def active_membership(self):
		for membership in Membership.objects.filter(member=self).order_by('-start_date', 'end_date'):
			if membership.is_active():
				return membership
		return None

	def paid_count(self):
		return DailyLog.objects.filter(member=self, payment='Bill').count()

	def first_visit(self):
		if Membership.objects.filter(member=self).count() > 0:
			return Membership.objects.filter(member=self).order_by('start_date')[0].start_date
		else:
			if DailyLog.objects.filter(member=self).count() > 0:
				return DailyLog.objects.filter(member=self).order_by('visit_date')[0].visit_date
			else:
				return None

	def host_daily_logs(self):
		return DailyLog.objects.filter(guest_of=self).order_by('-visit_date')

	def member_since(self):
		first = self.first_visit()
		if first == None: return None
		return timezone.localtime(timezone.now()) - datetime.combine(first, time(0,0,0))

	def last_visit(self):
		if DailyLog.objects.filter(member=self).count() > 0:
			return DailyLog.objects.filter(member=self).latest('visit_date').visit_date
		else:
			if Membership.objects.filter(member=self, end_date__isnull=False).count() > 0:
				return Membership.objects.filter(member=self, end_date__isnull=False).latest('end_date').end_date
			else:
				return None

	def membership_type(self):
		# First check for existing monthly
		memberships = Membership.objects.filter(member=self)
		if self.last_membership():
			last_monthly = self.last_membership()
			if last_monthly.end_date == None or last_monthly.end_date > timezone.now().date():
				return last_monthly.membership_plan
			else:
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

	def has_desk(self):
		m = self.last_membership()
		if not m: return False
		if m.is_active():
			return m.has_desk
		return False

	def is_guest(self):
		m = self.last_membership()
		if m and m.is_active() and m.guest_of:
			return m.guest_of
		return None

	def has_valid_billing(self):
		host = self.is_guest()
		if host:
			return host.has_valid_billing()
		return self.valid_billing
		
	def guests(self):
		guests = []
		for membership in Membership.objects.filter(guest_of=self):
			if membership.is_active():
				guests.append(membership.member)
		return guests

	def onboard_tasks_status(self):
		"""
		Returns an array of tuples: (Onboard_Task, Onboard_Task_Completed) for this member.
		Onboard_Task_Completed may be None.
		"""
		return [(task, Onboard_Task_Completed.objects.for_member(task, self)) for task in Onboard_Task.objects.all()]

	def onboard_tasks_to_complete(self):
		return Onboard_Task.objects.count() - Onboard_Task_Completed.objects.filter(member=self).count()

	def qualifies_for_exit_tasks(self):
		last_log = self.last_membership()
		if not last_log or last_log.end_date == None: return False
		return last_log.end_date < timezone.now().date()

	def exit_tasks_status(self):
		"""
		Returns an array of tuples: (ExitTask, ExitTaskCompleted) for this member.
		ExitCompleted may be None.
		"""
		if not self.qualifies_for_exit_tasks(): return []
		return [(task, ExitTaskCompleted.objects.for_member(task, self)) for task in ExitTask.objects.all()]

	def exit_tasks_to_complete(self):
		if not self.qualifies_for_exit_tasks(): return 0
		return ExitTask.objects.count() - ExitTaskCompleted.objects.filter(member=self).count()

	def __str__(self): return '%s %s' % (smart_str(self.user.first_name), smart_str(self.user.last_name))

	@models.permalink
	def get_absolute_url(self):
		return ('staff.views.member_detail', (), { 'member_id':self.id })

	class Meta:
		ordering = ['user__first_name', 'user__last_name']
		get_latest_by = "last_modified"

# If a User gets created, make certain that it has a Member record
def user_save_callback(sender, **kwargs):
	user = kwargs['instance']
	created = kwargs['created']
	if Member.objects.filter(user=user).count() > 0: return
	Member.objects.create(user=user)

post_save.connect(user_save_callback, sender=User)

# Add some handy methods to Django's User object
User.get_profile = lambda self: Member.objects.get_or_create(user=self)[0]
User.get_absolute_url = lambda self: Member.objects.get(user=self).get_absolute_url()
User.profile = property(User.get_profile)

class DailyLog(models.Model):
	"""A visit by a member"""
	member = models.ForeignKey(Member, verbose_name="Member", unique_for_date="visit_date", related_name="daily_logs")
	visit_date = models.DateField("Date")
	payment = models.CharField("Payment", max_length=5, choices=PAYMENT_CHOICES)
	guest_of = models.ForeignKey(Member, verbose_name="Guest Of", related_name="guest_of", blank=True, null=True)
	note = models.CharField("Note", max_length=128, blank="True")
	created = models.DateTimeField(auto_now_add=True, default=timezone.localtime(timezone.now()))

	def __str__(self):
		return '%s - %s' % (self.visit_date, self.member)

	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_dailylog_change', args=[self.id])

	class Meta:
		verbose_name = "Daily Log"
		ordering = ['-visit_date', '-created']

class MembershipPlan(models.Model):
	"""Options for monthly membership"""
	name = models.CharField(max_length=16)
	description = models.CharField(max_length=128, blank=True, null=True)
	monthly_rate = models.IntegerField(default=0)
	daily_rate = models.IntegerField(default=0)
	dropin_allowance = models.IntegerField(default=0)
	deposit_amount = models.IntegerField(default=0)
	has_desk = models.NullBooleanField(default=False)

	def __str__(self): return self.name

	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_membershipplan_change', args=[self.id])

	class Meta:
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
			deposit_amount=membership_plan.deposit_amount, has_desk=membership_plan.has_desk, guest_of=guest_of)

class Membership(models.Model):
	"""A membership level which is billed monthly"""
	member = models.ForeignKey(Member, related_name="memberships")
	membership_plan = models.ForeignKey(MembershipPlan, null=True)
	start_date = models.DateField()
	end_date = models.DateField(blank=True, null=True)
	monthly_rate = models.IntegerField(default=0)
	dropin_allowance = models.IntegerField(default=0)
	daily_rate = models.IntegerField(default=0)
	deposit_amount = models.IntegerField(default=0)
	has_desk = models.NullBooleanField(default=False)
	guest_of = models.ForeignKey(Member, blank=True, null=True, related_name="monthly_guests")
	note = models.CharField(max_length=128, blank=True, null=True)

	objects = MembershipManager()

	def save(self, *args, **kwargs):
		if Membership.objects.by_date(self.start_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
			raise Exception('Already have a Membership for that start date')
		if self.end_date and Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
			raise Exception('Already have a Membership for that end date: %s' % Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member))
		if self.end_date and self.start_date > self.end_date:
			raise Exception('A Membership cannot start after it ends')
		super(Membership, self).save(*args, **kwargs)

	def is_active(self, on_date=date.today()):
		if self.start_date > on_date: return false
		return self.end_date == None or self.end_date >= on_date

	def is_anniversary_day(self, test_date):
		# Do something smarter if we're at the end of February
		if test_date.month == 2 and test_date.day == 28:
			if self.start_date.day >= 29: return True

		# 30 days has September, April, June, and November
		if self.start_date.day == 31 and test_date.day == 30:
			if test_date.month in [9, 4, 6, 11]: return True
		return test_date.day == self.start_date.day

	def __str__(self):
		return '%s - %s' % (self.start_date, self.member)

	def get_admin_url(self):
		return urlresolvers.reverse('admin:staff_membership_change', args=[self.id])

	class Meta:
		verbose_name = "Membership"
		verbose_name_plural = "Memberships"
		ordering = ['start_date'];

class ExitTaskManager(models.Manager):
	def uncompleted_count(self):
		count = 0;
		for t in ExitTask.objects.all():
			count += len(t.uncompleted_members())
		return count

class ExitTask(models.Model):
	"""Tasks which are to be completed when a monthly member ends their memberships."""
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=512)
	order = models.SmallIntegerField()
	has_desk_only = models.BooleanField(verbose_name="Only Applies to Members with Desks")
	objects = ExitTaskManager()

	def uncompleted_members(self):
		eligable_members = [member for member in Member.objects.filter(memberships__isnull=False).exclude(exittaskcompleted__task=self).distinct() if not member.is_active()]
		if self.has_desk_only:
			eligable_members = [member for member in eligable_members if member.has_desk()]
		return eligable_members

	def completed_members(self):
		return Member.objects.filter(memberships__end_date__gt=timezone.now().date()).filter(exittaskcompleted__task=self).distinct()

	def __str__(self): return self.name

	@models.permalink
	def get_absolute_url(self): return ('staff.views.exit_task', (), { 'id':self.id })

	class Meta:
		ordering = ['order']

class ExitTaskCompletedManager(models.Manager):
	def for_member(self, task, member):
		if self.filter(task=task, member=member).count() == 0: return None
		return self.filter(task=task, member=member)[0]

class ExitTaskCompleted(models.Model):
	"""A record that an exit task has been completed"""
	member = models.ForeignKey(Member)
	task = models.ForeignKey(ExitTask)
	completed_date = models.DateField(auto_now_add=True)
	objects = ExitTaskCompletedManager()
	def __str__(self): return '%s - %s - %s' % (self.member, self.task, self.completed_date)

class Onboard_Task_Manager(models.Manager):
	def uncompleted_count(self):
		count = 0;
		for t in Onboard_Task.objects.all():
			count += t.uncompleted_members().count()
		return count

class Onboard_Task(models.Model):
	"""Tasks which are to be completed when a new member joins the space."""
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=512)
	order = models.SmallIntegerField()
	has_desk_only = models.BooleanField(verbose_name="Only Applies to Members with Desks")
	objects = Onboard_Task_Manager()

	def uncompleted_members(self):
		eligable_members = Member.objects.active_members()
		if self.has_desk_only:
			eligable_members = eligable_members.filter(memberships__has_desk=True)
		return eligable_members.exclude(onboard_task_completed__task=self).distinct()

	def completed_members(self):
		return Member.objects.filter(onboard_task_completed=self).distinct()

	def __str__(self): return self.name

	@models.permalink
	def get_absolute_url(self): return ('staff.views.onboard_task', (), { 'id':self.id })

	class Meta:
		verbose_name = "On-boarding Task"
		ordering = ['order']

class Onboard_Task_Completed_Manager(models.Manager):
	def for_member(self, task, member):
		if self.filter(task=task, member=member).count() == 0: return None
		return self.filter(task=task, member=member)[0]

class Onboard_Task_Completed(models.Model):
	"""A record that an onboard task has been completed"""
	member = models.ForeignKey(Member)
	task = models.ForeignKey(Onboard_Task)
	completed_date = models.DateField(auto_now_add=True)
	objects = Onboard_Task_Completed_Manager()

	class Meta:
		unique_together = ("member", "task")

	def __str__(self): return '%s - %s' % (self.member, self.completed_date)

class SentEmailLog(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	member = models.ForeignKey('Member', null=True)
	recipient = models.EmailField()
	subject = models.CharField(max_length=128, blank=True, null=True)
	success = models.NullBooleanField(blank=False, null=False, default=False)
	note = models.TextField(blank=True, null=True)
	def __str__(self): return '%s: %s' % (self.created, self.recipient)

# Copyright 2009, 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
