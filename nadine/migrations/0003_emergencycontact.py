# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import django_localflavor_us.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nadine', '0002_auto_20150623_1653'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmergencyContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254, blank=True)),
                ('relationship', models.CharField(max_length=254, blank=True)),
                ('phone', django_localflavor_us.models.PhoneNumberField(max_length=20, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
        ),
    ]
