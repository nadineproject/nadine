from datetime import datetime, time, date
import pprint, traceback
from django.db import models
from django.contrib.localflavor.us.models import USStateField, PhoneNumberField
from django.contrib import admin
from django.core import urlresolvers
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models.signals import post_save

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

PAYMENT_CHOICES = (
    ('Bill', 'Billable'),
    ('Trial', 'Free Trial'),
    ('Waved', 'Payment Waved'),
)

MEMBERSHIP_CHOICES = (
    ('Basic', 'Basic'),
    ('PT5', 'Part Time 5'),
    ('PT10', 'Part Time 10'),
    ('PT15', 'Part Time 15'),
    ('Regular', 'Regular'),
    ('Resident', 'Resident'),
    ('ISP', 'Internet Service'),
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
      if not ended: return None
      return datetime.date(ended)

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
      future_ending = Q(memberships__end_date__gt=date.today())
      return Member.objects.exclude(memberships__isnull=True).filter(unending | future_ending).distinct()
   
   def members_by_membership_type(self, membership_type):
      return [log.member for log in Membership.objects.filter(plan=membership_type).filter(Q(end_date__isnull=True) | Q(end_date__gt=date.today())).distinct().order_by('member__user__first_name')]

   def members_by_neighborhood(self, hood, active_only=True):
      if active_only:
         return Member.objects.filter(neighborhood=hood).filter(memberships__isnull=False).filter(Q(memberships__end_date__isnull=True) | Q(memberships__end_date__gt=date.today())).distinct()
      else:
         return Member.objects.filter(neighborhood=hood)
         
   def search(self, search_string):
      terms = search_string.split()
      if len(terms) == 0: return None;
      fname_query = Q(user__first_name__icontains=terms[0]) 
      lname_query = Q(user__last_name__icontains=terms[0]) 
      for term in terms[1:]:
         fname_query = fname_query | Q(user__first_name__icontains=term) 
         lname_query = lname_query | Q(user__last_name__icontains=term) 
      return self.filter(fname_query | lname_query)

   def get_by_natural_key(self, user_id): return self.get(user__id=user_id)

class Member(models.Model):
   """A person who has used the space and may or may not have a monthly membership"""
   objects = MemberManager()

   user = models.ForeignKey(User, unique=True, blank=False)
   email2 = models.EmailField("Alternate Email", blank=True, null=True)
   phone = PhoneNumberField(blank=True, null=True)
   phone2 = PhoneNumberField("Alternate Phone", blank=True, null=True)
   website = models.URLField(blank=True, null=True, verify_exists=False)
   gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
   howHeard = models.ForeignKey(HowHeard, blank=True, null=True)
   industry = models.ForeignKey(Industry, blank=True, null=True)
   neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True)
   has_kids = models.NullBooleanField(blank=True, null=True)
   self_employed = models.NullBooleanField(blank=True, null=True)
   company_name = models.CharField(max_length=128, blank=True, null=True)
   promised_followup = models.DateField(blank=True, null=True)
   last_modified = models.DateField(auto_now=True, editable=False)
   notes = models.TextField(blank=True, null=True)
   photo = models.ImageField(upload_to='member_photo', blank=True, null=True)

   @property
   def first_name(self): return self.user.first_name

   @property
   def last_name(self): return self.user.last_name
   
   @property
   def email(self): return self.user.email

   @property
   def full_name(self):
      return '%s %s' % (self.user.first_name, self.user.last_name)

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
      
   def paid_count(self):
      return DailyLog.objects.filter(member=self, payment='Bill').count()

   def first_visit(self):
      if DailyLog.objects.filter(member=self).count() > 0:
         return DailyLog.objects.filter(member=self).order_by('visit_date')[0].visit_date
      else:
         if Membership.objects.filter(member=self).count() > 0:
            return Membership.objects.filter(member=self).order_by('start_date')[0].start_date
         else:
            return None

   def host_daily_logs(self):
      return DailyLog.objects.filter(guest_of=self).order_by('-visit_date')

   def member_since(self):
      first = self.first_visit()
      if first == None: return None
      return datetime.now() - datetime.combine(first, time(0,0,0))

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
      if memberships.count() > 0:
         last_monthly = self.last_membership()
         if last_monthly.end_date == None or last_monthly.end_date > date.today():
            return last_monthly.plan
         else:
            return "Ex" + last_monthly.plan
            
      # Now check daily logs
      if DailyLog.objects.filter(member=self).count() > 0:
         # Quantify the daily
         p = self.paid_count()
         if p == 0:
            return "Free Trial Only"
         elif p > 5:
            return "Regular Daily"
         else:
            return "Dabbler"
      else:
         # Never visited
         return "No drop-ins"

   def is_monthly(self):
      last_log = self.last_membership()
      if  not last_log: return False
      return last_log.end_date == None or last_log.end_date >= date.today()
   
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
      return last_log.end_date < date.today()

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

   def __str__(self): return '%s %s' % (self.user.first_name, self.user.last_name)

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
   
   created = models.DateTimeField(auto_now_add=True, default=datetime.now())

   def __str__(self):
      return '%s - %s' % (self.visit_date, self.member)

   def get_admin_url(self):
      return urlresolvers.reverse('admin:staff_dailylog_change', args=[self.id])

   class Meta:
      verbose_name = "Daily Log"
      ordering = ['-visit_date', '-created']

class Membership_Manager(models.Manager):
   def by_date(self, target_date):
      return self.filter(start_date__lte=target_date).filter(Q(end_date__isnull=True) | Q(end_date__gte=target_date))

class Membership(models.Model):
   """A membership level which is billed monthly"""
   member = models.ForeignKey(Member, related_name="memberships")
   plan = models.CharField(max_length=8, choices=MEMBERSHIP_CHOICES)
   start_date = models.DateField()
   end_date = models.DateField(blank=True, null=True)
   rate = models.IntegerField(default=0)
   note = models.CharField(max_length=128, blank=True, null=True)
   guest_dropins = models.IntegerField(default=0)
   guest_of = models.ForeignKey(Member, blank=True, null=True, related_name="monthly_guests")

   objects = Membership_Manager()

   def save(self, *args, **kwargs):
      if Membership.objects.by_date(self.start_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
         raise Exception('Already have a Membership for that start date')
      if self.end_date and Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member).count() != 0:
         raise Exception('Already have a Membership for that end date: %s' % Membership.objects.by_date(self.end_date).exclude(pk=self.pk).filter(member=self.member))
      if self.end_date and self.start_date > self.end_date:
         raise Exception('A Membership cannot start after it ends')
      super(Membership, self).save(*args, **kwargs)

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

class ExitTask(models.Model):
   """Tasks which are to be completed when a monthly member ends their memberships."""
   name = models.CharField(max_length=64)
   description = models.CharField(max_length=512)
   order = models.SmallIntegerField()

   def uncompleted_members(self):
      return [member for member in Member.objects.filter(memberships__isnull=False).exclude(exittaskcompleted__task=self).distinct() if not member.is_monthly()]

   def completed_members(self):
      return Member.objects.filter(memberships__end_date__gt=date.today()).filter(exittaskcompleted__task=self).distinct()

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

class Onboard_Task(models.Model):
   """Tasks which are to be completed when a new member joins the space."""
   name = models.CharField(max_length=64)
   description = models.CharField(max_length=512)
   order = models.SmallIntegerField()
   monthly_only = models.BooleanField()

   def uncompleted_members(self):
      if self.monthly_only:
         eligable_members = Member.objects.filter(memberships__start_date__isnull=False).filter(Q(memberships__end_date__gt=date.today()) | Q(memberships__end_date__isnull=True))
      else:
         eligable_members = Member.objects.all()
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

   def __str__(self): return '%s - %s - %s' % (self.member, self.task, self.completed_date)

# Copyright 2009, 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
