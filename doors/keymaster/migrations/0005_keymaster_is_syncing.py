# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keymaster', '0004_gatekeeperlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='keymaster',
            name='is_syncing',
            field=models.BooleanField(default=False),
        ),
    ]
