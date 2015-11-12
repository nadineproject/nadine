# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hid', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gatekeeper',
            old_name='success_ts',
            new_name='sync_ts',
        ),
    ]
