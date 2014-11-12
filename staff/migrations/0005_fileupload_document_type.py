# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0004_fileupload'),
    ]

    operations = [
        migrations.AddField(
            model_name='fileupload',
            name='document_type',
            field=models.CharField(default=None, max_length=200, null=True, blank=True, choices=[(b'Member_Information', b'Member Information'), (b'Member_Agreement', b'Membership Agreement'), (b'Key_Agreement', b'Key Holder Agreement'), (b'Event_Host_Agreement', b'Event Host Agreement')]),
            preserve_default=True,
        ),
    ]
