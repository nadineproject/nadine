# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, time
from django.utils import timezone
from django.db import models, migrations
from django.db.models import Q
from django.conf import settings

# Copied over from the model
PAPERWORK = "paperwork"
MEMBER_INFO = "member_info"
MEMBER_AGREEMENT = "member_agreement"
TAKE_PHOTO = "take_photo"
UPLOAD_PHOTO = "upload_hoto"
POST_PHOTO = "post_photo"
ORIENTATION = "orientation"
KEY_AGREEMENT = "key_agreement"
STALE_MEMBER = "stale_member"
INVALID_BILLING = "invalid_billing"
REMOVE_PHOTO = "remove_photo"
RETURN_DOOR_KEY = "return_door_key"
RETURN_DESK_KEY = "return_desk_key"


def forward(apps, schema_editor):
    Onboard_Task = apps.get_model("nadine", "Onboard_Task")
    Onboard_Task_Completed = apps.get_model("nadine", "Onboard_Task_Completed")
    ExitTask = apps.get_model("nadine", "ExitTask")
    ExitTaskCompleted = apps.get_model("nadine", "ExitTaskCompleted")
    MemberAlert = apps.get_model("nadine", "MemberAlert")
    #Member = apps.get_model("nadine", "Member")
    #Membership = apps.get_model("nadine", "Membership")
    #User = apps.get_model("auth", "User")

    task_map = (
        (PAPERWORK, Onboard_Task.objects.filter(name="Received Paperwork")),
        (MEMBER_INFO, Onboard_Task.objects.filter(name="Enter & File Member Information")),
        (MEMBER_AGREEMENT, Onboard_Task.objects.filter(name="Sign Membership Agreement")),
        (TAKE_PHOTO, Onboard_Task.objects.filter(name="Take Photo")),
        (UPLOAD_PHOTO, Onboard_Task.objects.filter(name="Upload Photo")),
        (POST_PHOTO, Onboard_Task.objects.filter(name="Print & Post Photo")),
        (ORIENTATION, Onboard_Task.objects.filter(name="New Member Orientation")),
    )

    exit_task_map = (
        (REMOVE_PHOTO, ExitTask.objects.filter(name="Remove Picture from Wall")),
        (RETURN_DOOR_KEY, ExitTask.objects.filter(name="Take Back Keycard")),
        (RETURN_DESK_KEY, ExitTask.objects.filter(name="Take Back Roller Drawer Key")),
    )

    fake_ts = timezone.make_aware(datetime(year=2015, month=01, day=01), timezone.get_current_timezone())

    print("\n    Migrating completed on-boarding tasks... ")
    for key, task in task_map:
        completed_tasks = Onboard_Task_Completed.objects.filter(task=task)
        for tc in completed_tasks:
            dt = datetime.combine(tc.completed_date, time())
            ts = timezone.make_aware(dt, timezone.get_current_timezone())
            resolved_by = tc.completed_by
            alert = MemberAlert.objects.create(key=key, user=tc.member.user, resolved_ts=ts, resolved_by=resolved_by)
            alert.created_ts = fake_ts
            alert.save()
        print("    - %s: %s alerts created" % (key, completed_tasks.count()))

    print("    Migrating completed exit tasks... ")
    for key, task in exit_task_map:
        completed_tasks = ExitTaskCompleted.objects.filter(task=task)
        for tc in completed_tasks:
            dt = datetime.combine(tc.completed_date, time())
            ts = timezone.make_aware(dt, timezone.get_current_timezone())
            alert = MemberAlert.objects.create(created_ts="01/01/15", key=key, user=tc.member.user, resolved_ts=ts)
            alert.created_ts = fake_ts
            alert.save()
        print("    - %s: %s alerts created" % (key, completed_tasks.count()))

    # TODO - Recently excited members?


def reverse(apps, schema_editor):
    pass

# This code violates the abstracted object model so this needs to be run manually after the data is migrated


def post_migration():
    from nadine.models import Member, MemberAlert
    for member in Member.objects.active_members():
        MemberAlert.objects.trigger_new_membership(member.user)
        member.resolve_alerts(MemberAlert.POST_PHOTO)
    MemberAlert.objects.trigger_nightly_check()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nadine', '0002_auto_20150210_1136'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberAlert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_ts', models.DateTimeField(auto_now_add=True)),
                ('key', models.CharField(max_length=16)),
                ('resolved_ts', models.DateTimeField(null=True)),
                ('muted_ts', models.DateTimeField(null=True)),
                ('note', models.TextField(null=True, blank=True)),
                ('muted_by', models.ForeignKey(related_name='muted_by', to=settings.AUTH_USER_MODEL, null=True)),
                ('resolved_by', models.ForeignKey(related_name='resolved_by', to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RunPython(forward, reverse_code=reverse),
    ]
