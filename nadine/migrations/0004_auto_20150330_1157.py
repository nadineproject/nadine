# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nadine', '0003_memberalert'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exittaskcompleted',
            name='member',
        ),
        migrations.RemoveField(
            model_name='exittaskcompleted',
            name='task',
        ),
        migrations.DeleteModel(
            name='ExitTask',
        ),
        migrations.DeleteModel(
            name='ExitTaskCompleted',
        ),
        migrations.RemoveField(
            model_name='onboard_task_completed',
            name='completed_by',
        ),
        migrations.RemoveField(
            model_name='onboard_task_completed',
            name='member',
        ),
        migrations.RemoveField(
            model_name='onboard_task_completed',
            name='task',
        ),
        migrations.DeleteModel(
            name='Onboard_Task',
        ),
        migrations.DeleteModel(
            name='Onboard_Task_Completed',
        ),
    ]
