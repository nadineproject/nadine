# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('nadine', '0004_auto_20150330_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='email2',
            field=models.EmailField(max_length=254, null=True, verbose_name=b'Alternate Email', blank=True),
        ),
        migrations.AlterField(
            model_name='member',
            name='user',
            field=models.OneToOneField(related_name='user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sentemaillog',
            name='recipient',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='bill',
            name='dropins',
            field=models.ManyToManyField(related_name='bills', to='nadine.DailyLog'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='guest_dropins',
            field=models.ManyToManyField(related_name='guest_bills', to='nadine.DailyLog'),
        ),
    ]
