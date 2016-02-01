# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keymaster', '0002_auto_20160111_1648'),
    ]

    operations = [
        migrations.AddField(
            model_name='keymaster',
            name='success_ts',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='door',
            name='door_type',
            field=models.CharField(max_length=16, choices=[(b'hid', b'Hid Controller'), (b'maypi', b'Maypi Controller'), (b'test', b'Test Controller')]),
        ),
    ]
