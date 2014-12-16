# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import nadine.models.core

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('staff', '0003_auto_20141017_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uploadTS', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=64)),
                ('content_type', models.CharField(max_length=64)),
                ('file', models.FileField(upload_to=nadine.models.core.user_file_upload_path)),
                ('uploaded_by', models.ForeignKey(related_name=b'uploaded_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
