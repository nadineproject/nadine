# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nadine', '0003_emergencycontact'),
    ]

    operations = [
        migrations.CreateModel(
            name='XeroContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('xero_id', models.CharField(max_length=64)),
                ('last_sync', models.DateTimeField(null=True, blank=True)),
                ('user', models.OneToOneField(related_name='xero_contact', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
        ),
    ]
