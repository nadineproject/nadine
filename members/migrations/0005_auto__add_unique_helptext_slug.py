# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding unique constraint on 'HelpText', fields ['slug']
        db.create_unique('members_helptext', ['slug'])


    def backwards(self, orm):
        # Removing unique constraint on 'HelpText', fields ['slug']
        db.delete_unique('members_helptext', ['slug'])


    models = {
        'members.helptext': {
            'Meta': {'object_name': 'HelpText'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {}),
            'template': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['members']