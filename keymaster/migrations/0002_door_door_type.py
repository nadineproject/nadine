# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keymaster', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='door',
            name='door_type',
            field=models.CharField(default='hid', max_length=16, choices=[(b'hid', b'Hid Controller'), (b'maypi', b'Maypi Controller')]),
            preserve_default=False,
        ),
    ]
