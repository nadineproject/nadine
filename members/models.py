from django.db import models
from django.db.models import Q
from django.contrib import admin

class HelpText(models.Model):
	title = models.CharField(max_length=128)
	text = models.TextField(blank=True, null=True)
	def __str__(self): return self.title