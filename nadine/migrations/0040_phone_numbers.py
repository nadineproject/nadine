# Generated by Django 3.2.1 on 2021-12-08 01:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nadine', '0039_auto_20200817_1328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emergencycontact',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(regex='^\\+?1?\\d{8,15}$')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(regex='^\\+?1?\\d{8,15}$')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone2',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(regex='^\\+?1?\\d{8,15}$')], verbose_name='Alternate Phone'),
        ),
    ]