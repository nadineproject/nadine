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
                ('name', models.CharField(unique=True, max_length=16)),
                ('username', models.CharField(max_length=32)),
                ('password', models.CharField(max_length=32)),
                ('ip_address', models.GenericIPAddressField()),
            ],
        ),
        migrations.CreateModel(
            name='DoorCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified_ts', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(unique=True, max_length=16)),
                ('created_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Gatekeeper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=64)),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('encryption_key', models.CharField(max_length=128)),
                ('access_ts', models.DateTimeField(auto_now=True)),
                ('success_ts', models.DateTimeField(null=True, blank=True)),
                ('is_enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='door',
            name='gatekeeper',
            field=models.ForeignKey(to='hid.Gatekeeper'),
        ),
    ]
