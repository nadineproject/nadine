# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0002_auto_20140911_1516'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bill',
            options={'ordering': ['-bill_date'], 'get_latest_by': 'bill_date'},
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-transaction_date']},
        ),
        migrations.RenameField(
            model_name='bill',
            old_name='created',
            new_name='bill_date',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='created',
            new_name='transaction_date',
        ),
    ]
