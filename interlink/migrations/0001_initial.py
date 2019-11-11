# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IncomingMail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('origin_address', models.EmailField(max_length=75)),
                ('sent_time', models.DateTimeField()),
                ('subject', models.TextField(blank=True)),
                ('body', models.TextField(null=True, blank=True)),
                ('html_body', models.TextField(null=True, blank=True)),
                ('original_message', models.TextField(blank=True)),
                ('state', models.CharField(default='raw', max_length=10, choices=[('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject')])),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailingList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('description', models.TextField(blank=True)),
                ('subject_prefix', models.CharField(max_length=1024, blank=True)),
                ('is_opt_out', models.BooleanField(default=False, help_text='True if new users should be automatically enrolled')),
                ('moderator_controlled', models.BooleanField(default=False, help_text='True if only the moderators can send mail to the list and can unsubscribe users.')),
                ('email_address', models.EmailField(max_length=75)),
                ('username', models.CharField(max_length=1024)),
                ('password', models.CharField(max_length=1024)),
                ('pop_host', models.CharField(max_length=1024)),
                ('pop_port', models.IntegerField(default=995)),
                ('smtp_host', models.CharField(max_length=1024)),
                ('smtp_port', models.IntegerField(default=587)),
                ('throttle_limit', models.IntegerField(default=0, help_text='The number of recipients in 10 minutes this mailing list is limited to. Default is 0, which means no limit.')),
                ('moderators', models.ManyToManyField(help_text='Users who will be sent moderation emails', related_name='moderated_mailing_lists', to=settings.AUTH_USER_MODEL, blank=True)),
                ('subscribers', models.ManyToManyField(related_name='subscribed_mailing_lists', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutgoingMail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('moderators_only', models.BooleanField(default=False)),
                ('subject', models.TextField(blank=True)),
                ('body', models.TextField(null=True, blank=True)),
                ('html_body', models.TextField(null=True, blank=True)),
                ('attempts', models.IntegerField(default=0)),
                ('last_attempt', models.DateTimeField(null=True, blank=True)),
                ('sent', models.DateTimeField(null=True, blank=True)),
                ('sent_recipients', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('mailing_list', models.ForeignKey(related_name='outgoing_mails', to='interlink.MailingList', on_delete=models.deletion.CASCADE)),
                ('original_mail', models.ForeignKey(default=None, blank=True, to='interlink.IncomingMail', on_delete=models.deletion.CASCADE, help_text='The incoming mail which caused this mail to be sent', null=True)),
            ],
            options={
                'ordering': ['-created'],
                'verbose_name_plural': 'outgoing mails',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='incomingmail',
            name='mailing_list',
            field=models.ForeignKey(related_name='incoming_mails', to='interlink.MailingList', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='incomingmail',
            name='owner',
            field=models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
    ]
