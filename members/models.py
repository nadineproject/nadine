from django.db import models
from django.db.models import Q
from django.contrib import admin

class HelpText(models.Model):
	title = models.CharField(max_length=128)
	template = models.TextField(blank=True, null=True)
	slug = models.CharField(max_length=16, unique=True)
	order = models.SmallIntegerField()
	def __str__(self): return self.title