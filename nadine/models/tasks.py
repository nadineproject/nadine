from django.db import models
from django.db.models import Q

from nadine.models.core import *

class ExitTaskManager(models.Manager):
	def uncompleted_count(self):
		count = 0;
		for t in ExitTask.objects.all():
			count += len(t.uncompleted_members())
		return count

	class Meta:
		app_label = 'nadine'

class ExitTask(models.Model):
	"""Tasks which are to be completed when a monthly member ends their memberships."""
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=512)
	order = models.SmallIntegerField()
	has_desk_only = models.BooleanField(verbose_name="Only Applies to Members with Desks", default=False)
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
		app_label = 'nadine'
		ordering = ['order']

class ExitTaskCompletedManager(models.Manager):
	def for_member(self, task, member):
		if self.filter(task=task, member=member).count() == 0: return None
		return self.filter(task=task, member=member)[0]

	class Meta:
		app_label = 'nadine'

class ExitTaskCompleted(models.Model):
	"""A record that an exit task has been completed"""
	member = models.ForeignKey(Member)
	task = models.ForeignKey(ExitTask)
	completed_date = models.DateField(auto_now_add=True)
	objects = ExitTaskCompletedManager()
	def __str__(self): return '%s - %s - %s' % (self.member, self.task, self.completed_date)

	class Meta:
		app_label = 'nadine'

class Onboard_Task_Manager(models.Manager):
	def uncompleted_count(self):
		count = 0;
		for t in Onboard_Task.objects.all():
			count += t.uncompleted_members().count()
		return count

		class Meta:
			app_label = 'nadine'

class Onboard_Task(models.Model):
	"""Tasks which are to be completed when a new member joins the space."""
	name = models.CharField(max_length=64)
	description = models.CharField(max_length=512)
	order = models.SmallIntegerField()
	has_desk_only = models.BooleanField(verbose_name="Only Applies to Members with Desks", default=False)
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
		app_label = 'nadine'
		verbose_name = "On-boarding Task"
		ordering = ['order']

class Onboard_Task_Completed_Manager(models.Manager):
	def for_member(self, task, member):
		if self.filter(task=task, member=member).count() == 0: return None
		return self.filter(task=task, member=member)[0]

	class Meta:
		app_label = 'nadine'

class Onboard_Task_Completed(models.Model):
	"""A record that an onboard task has been completed"""
	member = models.ForeignKey(Member)
	task = models.ForeignKey(Onboard_Task)
	completed_date = models.DateField(auto_now_add=True)
	completed_by = models.ForeignKey(User, null=True)
	objects = Onboard_Task_Completed_Manager()

	class Meta:
		app_label = 'nadine'
		unique_together = ("member", "task")

	def __str__(self): 
		if self.completed_by:
			return '%s - %s on %s by %s' % (self.member, self.task, self.completed_date, self.completed_by)
		else:
			return '%s - %s on %s' % (self.member, self.task, self.completed_date)
