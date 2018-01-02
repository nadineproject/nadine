# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MOTD',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_ts', models.DateTimeField()),
                ('end_ts', models.DateTimeField()),
                ('message', models.TextField()),
                ('delay_ms', models.SmallIntegerField(default=5000)),
            ],
        ),
    ]
