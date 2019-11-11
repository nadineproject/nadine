# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings

import taggit.managers
import django_localflavor_us.models

import nadine.models


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bill_date', models.DateField()),
                ('amount', models.DecimalField(max_digits=7, decimal_places=2)),
                ('new_member_deposit', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-bill_date'],
                'get_latest_by': 'bill_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BillingLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('started', models.DateTimeField(auto_now_add=True)),
                ('ended', models.DateTimeField(null=True, blank=True)),
                ('successful', models.BooleanField(default=False)),
                ('note', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['-started'],
                'get_latest_by': 'started',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DailyLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('visit_date', models.DateField(verbose_name='Date')),
                ('payment', models.CharField(max_length=5, verbose_name='Payment', choices=[('Bill', 'Billable'), ('Trial', 'Free Trial'), ('Waved', 'Payment Waved')])),
                ('note', models.CharField(max_length=128, verbose_name='Note', blank='True')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-visit_date', '-created'],
                'verbose_name': 'Daily Log',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExitTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=512)),
                ('order', models.SmallIntegerField()),
                ('has_desk_only', models.BooleanField(default=False, verbose_name='Only Applies to Members with Desks')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExitTaskCompleted',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('completed_date', models.DateField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uploadTS', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=64)),
                ('content_type', models.CharField(max_length=64)),
                ('file', models.FileField(upload_to=nadine.models.user_file_upload_path)),
                ('document_type', models.CharField(default=None, max_length=200, null=True, blank=True, choices=[('Member_Information', 'Member Information'), ('Member_Agreement', 'Membership Agreement'), ('Key_Agreement', 'Key Holder Agreement'), ('Event_Host_Agreement', 'Event Host Agreement')])),
                ('uploaded_by', models.ForeignKey(related_name='uploaded_by', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HowHeard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Industry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Industry',
                'verbose_name_plural': 'Industries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email2', models.EmailField(max_length=75, null=True, verbose_name='Alternate Email', blank=True)),
                ('phone', django_localflavor_us.models.PhoneNumberField(max_length=20, null=True, blank=True)),
                ('phone2', django_localflavor_us.models.PhoneNumberField(max_length=20, null=True, verbose_name='Alternate Phone', blank=True)),
                ('address1', models.CharField(max_length=128, blank=True)),
                ('address2', models.CharField(max_length=128, blank=True)),
                ('city', models.CharField(max_length=128, blank=True)),
                ('state', models.CharField(max_length=2, blank=True)),
                ('zipcode', models.CharField(max_length=5, blank=True)),
                ('url_personal', models.URLField(null=True, blank=True)),
                ('url_professional', models.URLField(null=True, blank=True)),
                ('url_facebook', models.URLField(null=True, blank=True)),
                ('url_twitter', models.URLField(null=True, blank=True)),
                ('url_linkedin', models.URLField(null=True, blank=True)),
                ('url_aboutme', models.URLField(null=True, blank=True)),
                ('url_github', models.URLField(null=True, blank=True)),
                ('gender', models.CharField(default='U', max_length=1, choices=[('U', 'Unknown'), ('M', 'Male'), ('F', 'Female'), ('O', 'Other')])),
                ('has_kids', models.NullBooleanField()),
                ('self_employed', models.NullBooleanField()),
                ('company_name', models.CharField(max_length=128, null=True, blank=True)),
                ('promised_followup', models.DateField(null=True, blank=True)),
                ('last_modified', models.DateField(auto_now=True)),
                ('photo', models.ImageField(null=True, upload_to=nadine.models.user_photo_path, blank=True)),
                ('valid_billing', models.BooleanField(default=False)),
                ('howHeard', models.ForeignKey(blank=True, to='nadine.HowHeard', null=True, on_delete=models.deletion.CASCADE)),
                ('industry', models.ForeignKey(blank=True, to='nadine.Industry', null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['user__first_name', 'user__last_name'],
                'get_latest_by': 'last_modified',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('note', models.TextField(null=True, blank=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.deletion.CASCADE)),
                ('member', models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField(db_index=True)),
                ('end_date', models.DateField(db_index=True, null=True, blank=True)),
                ('monthly_rate', models.IntegerField(default=0)),
                ('dropin_allowance', models.IntegerField(default=0)),
                ('daily_rate', models.IntegerField(default=0)),
                ('has_desk', models.BooleanField(default=False)),
                ('has_key', models.BooleanField(default=False)),
                ('has_mail', models.BooleanField(default=False)),
                ('guest_of', models.ForeignKey(related_name='monthly_guests', blank=True, to='nadine.Member', null=True, on_delete=models.deletion.CASCADE)),
                ('member', models.ForeignKey(related_name='memberships', to='nadine.Member', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['start_date'],
                'verbose_name': 'Membership',
                'verbose_name_plural': 'Memberships',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MembershipPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=16)),
                ('description', models.CharField(max_length=128, null=True, blank=True)),
                ('monthly_rate', models.IntegerField(default=0)),
                ('daily_rate', models.IntegerField(default=0)),
                ('dropin_allowance', models.IntegerField(default=0)),
                ('has_desk', models.NullBooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Membership Plan',
                'verbose_name_plural': 'Membership Plans',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Neighborhood',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Onboard_Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=512)),
                ('order', models.SmallIntegerField()),
                ('has_desk_only', models.BooleanField(default=False, verbose_name='Only Applies to Members with Desks')),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'On-boarding Task',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Onboard_Task_Completed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('completed_date', models.DateField(auto_now_add=True)),
                ('completed_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.deletion.CASCADE)),
                ('member', models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE)),
                ('task', models.ForeignKey(to='nadine.Onboard_Task', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SecurityDeposit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('received_date', models.DateField()),
                ('returned_date', models.DateField(null=True, blank=True)),
                ('amount', models.PositiveSmallIntegerField(default=0)),
                ('note', models.CharField(max_length=128, null=True, blank=True)),
                ('member', models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SentEmailLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.EmailField(max_length=75)),
                ('subject', models.CharField(max_length=128, null=True, blank=True)),
                ('success', models.NullBooleanField(default=False)),
                ('note', models.TextField(null=True, blank=True)),
                ('member', models.ForeignKey(to='nadine.Member', null=True, on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SpecialDay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('month', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('day', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('description', models.CharField(max_length=128, null=True, blank=True)),
                ('member', models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('transaction_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='open', max_length=10, choices=[('open', 'Open'), ('closed', 'Closed')])),
                ('amount', models.DecimalField(max_digits=7, decimal_places=2)),
                ('note', models.TextField(null=True, blank=True)),
                ('bills', models.ManyToManyField(related_name='transactions', to='nadine.Bill')),
                ('member', models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE)),
            ],
            options={
                'ordering': ['-transaction_date'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_ts', models.DateTimeField(auto_now_add=True)),
                ('key', models.CharField(max_length=16)),
                ('resolved_ts', models.DateTimeField(null=True)),
                ('muted_ts', models.DateTimeField(null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('muted_by', models.ForeignKey(null=True, related_name='muted_by', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('resolved_by', models.ForeignKey(null=True, related_name='resolved_by', to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='onboard_task_completed',
            unique_together=set([('member', 'task')]),
        ),
        migrations.AddField(
            model_name='membership',
            name='membership_plan',
            field=models.ForeignKey(to='nadine.MembershipPlan', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='neighborhood',
            field=models.ForeignKey(blank=True, to='nadine.Neighborhood', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='member',
            name='user',
            field=models.ForeignKey(related_name='user', to=settings.AUTH_USER_MODEL, unique=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exittaskcompleted',
            name='member',
            field=models.ForeignKey(to='nadine.Member', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='exittaskcompleted',
            name='task',
            field=models.ForeignKey(to='nadine.ExitTask', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dailylog',
            name='guest_of',
            field=models.ForeignKey(related_name='guest_of', verbose_name='Guest Of', blank=True, to='nadine.Member', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dailylog',
            name='member',
            field=models.ForeignKey(related_name='daily_logs', verbose_name='Member', to='nadine.Member', unique_for_date='visit_date', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='dropins',
            field=models.ManyToManyField(related_name='bills', null=True, to='nadine.DailyLog', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='guest_dropins',
            field=models.ManyToManyField(related_name='guest_bills', null=True, to='nadine.DailyLog', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='member',
            field=models.ForeignKey(related_name='bills', to='nadine.Member', on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='membership',
            field=models.ForeignKey(blank=True, to='nadine.Membership', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bill',
            name='paid_by',
            field=models.ForeignKey(related_name='guest_bills', blank=True, to='nadine.Member', null=True, on_delete=models.deletion.CASCADE),
            preserve_default=True,
        ),
    ]
