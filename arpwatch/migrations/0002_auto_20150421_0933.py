# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arpwatch', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arplog',
            name='ip_address',
            field=models.GenericIPAddressField(db_index=True),
        ),
        migrations.AlterField(
            model_name='userremoteaddr',
            name='ip_address',
            field=models.GenericIPAddressField(),
        ),
    ]
