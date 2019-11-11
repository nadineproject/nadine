# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keymaster', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doorevent',
            name='code',
            field=models.CharField(max_length=16, null=True),
        ),
    ]
