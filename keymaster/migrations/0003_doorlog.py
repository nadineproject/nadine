# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('keymaster', '0002_door_door_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoorLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('code', models.CharField(max_length=16)),
                ('event_type', models.CharField(default=b'0', max_length=1, choices=[(b'0', b'Unknown'), (b'1', b'Unrecognized Card'), (b'2', b'Access Granted'), (b'2', b'Access Denied'), (b'4', b'Door Locked'), (b'5', b'Door Unlocked')])),
                ('event_description', models.CharField(max_length=256)),
                ('door', models.ForeignKey(to='keymaster.Door')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
