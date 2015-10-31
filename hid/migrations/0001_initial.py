# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Door',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=128)),
                ('stub', models.CharField(max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name='DoorCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField(auto_now_add=True)),
                ('modified_ts', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(unique=True, max_length=16, db_index=True)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField(null=True, blank=True)),
                ('sync_ts', models.DateTimeField(null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('door', models.ForeignKey(to='hid.Door')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Gatekeeper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('encryption_key', models.CharField(max_length=128)),
                ('access_ts', models.DateTimeField(auto_now=True)),
                ('is_enabled', models.BooleanField(default=False)),
            ],
        ),
    ]
