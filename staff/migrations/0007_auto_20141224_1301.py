# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import staff.models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0006_auto_20141118_1225'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='url_biznik',
        ),
        migrations.AlterField(
            model_name='member',
            name='photo',
            field=models.ImageField(null=True, upload_to=staff.models.user_photo_path, blank=True),
            preserve_default=True,
        ),
    ]
