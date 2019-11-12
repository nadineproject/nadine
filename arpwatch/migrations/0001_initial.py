# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArpLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('runtime', models.DateTimeField(db_index=True)),
                ('ip_address', models.IPAddressField(db_index=True)),
            ],
            options={
                'ordering': ['-runtime'],
                'get_latest_by': 'runtime',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('file_name', models.CharField(max_length=32, db_index=True)),
                ('success', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('device_name', models.CharField(max_length=32, null=True, blank=True)),
                ('mac_address', models.CharField(unique=True, max_length=17, db_index=True)),
                ('ignore', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserRemoteAddr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('logintime', models.DateTimeField()),
                ('ip_address', models.IPAddressField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['-logintime'],
                'get_latest_by': 'logintime',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='arplog',
            name='device',
            field=models.ForeignKey(to='arpwatch.UserDevice', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
    ]
