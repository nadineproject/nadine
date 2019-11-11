# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nadine', '0005_nullable_valid_billing'),
    ]

    operations = [
        migrations.AddField(
            model_name='membershipplan',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
    ]
