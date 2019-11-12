# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nadine', '0004_xerocontact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='valid_billing',
            field=models.NullBooleanField(),
        ),
    ]
