from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.contrib.auth.models import User

class HelpText(models.Model):
	title = models.CharField(max_length=128)
	template = models.TextField(blank=True, null=True)
	slug = models.CharField(max_length=16, unique=True)
	order = models.SmallIntegerField()
	def __str__(self): return self.title
	
class UserNotification(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	notify_user = models.ForeignKey(User, related_name="notify", blank=False)
	target_user = models.ForeignKey(User, related_name="target", blank=False)
	sent_date = models.DateTimeField(blank=True, null=True, default=None)
