# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exittask',
            name='has_desk_only',
            field=models.BooleanField(default=False, verbose_name=b'Only Applies to Members with Desks'),
        ),
        migrations.AlterField(
            model_name='onboard_task',
            name='has_desk_only',
            field=models.BooleanField(default=False, verbose_name=b'Only Applies to Members with Desks'),
        ),
    ]
