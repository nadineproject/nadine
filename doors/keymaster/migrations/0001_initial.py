# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Door',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=16)),
                ('door_type', models.CharField(max_length=16, choices=[('hid', 'Hid Controller'), ('maypi', 'Maypi Controller')])),
                ('username', models.CharField(max_length=32)),
                ('password', models.CharField(max_length=32)),
                ('ip_address', models.GenericIPAddressField()),
            ],
        ),
        migrations.CreateModel(
            name='DoorCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified_ts', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(unique=True, max_length=16)),
                ('created_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='DoorEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField()),
                ('code', models.CharField(max_length=16)),
                ('event_type', models.CharField(default='0', max_length=1, choices=[('0', 'Unknown Command'), ('1', 'Unrecognized Card'), ('2', 'Access Granted'), ('3', 'Access Denied'), ('4', 'Door Locked'), ('5', 'Door Unlocked')])),
                ('event_description', models.CharField(max_length=256)),
                ('door', models.ForeignKey(to='keymaster.Door', on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Keymaster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=64)),
                ('gatekeeper_ip', models.GenericIPAddressField(unique=True)),
                ('encryption_key', models.CharField(max_length=128)),
                ('access_ts', models.DateTimeField(auto_now=True)),
                ('sync_ts', models.DateTimeField(null=True, blank=True)),
                ('is_enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='door',
            name='keymaster',
            field=models.ForeignKey(to='keymaster.Keymaster', on_delete=models.deletion.CASCADE),
        ),
    ]
