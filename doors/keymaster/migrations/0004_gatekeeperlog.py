# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keymaster', '0003_auto_20160201_1310'),
    ]

    operations = [
        migrations.CreateModel(
            name='GatekeeperLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('resolved', models.BooleanField(default=False)),
                ('message', models.TextField()),
                ('keymaster', models.ForeignKey(to='keymaster.Keymaster', on_delete=models.deletion.CASCADE)),
            ],
        ),
    ]
