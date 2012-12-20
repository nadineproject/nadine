# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.rename_column('members_helptext', 'text', 'template')
        db.add_column('members_helptext', 'slug',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=16, blank=True),
                      keep_default=False)
        db.add_column('members_helptext', 'order',
                      self.gf('django.db.models.fields.SmallIntegerField')(default=0),
                      keep_default=False)

    def backwards(self, orm):
        db.rename_column('members_helptext', 'template', 'text')
        db.delete_column('members_helptext', 'slug')
        db.delete_column('members_helptext', 'order')


    models = {
        'members.helptext': {
            'Meta': {'object_name': 'HelpText'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {}),
            'template': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['members']