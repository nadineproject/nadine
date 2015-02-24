# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
	DailyLog = apps.get_model("nadine", "DailyLog")
	for l in DailyLog.objects.filter(payment="Waved"):
		l.payment = "Waive"
		l.save()

class Migration(migrations.Migration):

	dependencies = [
		('nadine', '0001_initial'),
	]

	operations = [
		migrations.AlterField(
			model_name='dailylog',
			name='payment',
			field=models.CharField(max_length=5, verbose_name=b'Payment', choices=[(b'Bill', b'Billable'), (b'Trial', b'Free Trial'), (b'Waive', b'Payment Waived')]),
			preserve_default=True,
		),
		migrations.RunPython(forward),
	]
