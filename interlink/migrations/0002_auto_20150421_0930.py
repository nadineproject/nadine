# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interlink', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incomingmail',
            name='origin_address',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='mailinglist',
            name='email_address',
            field=models.EmailField(max_length=254),
        ),
    ]
