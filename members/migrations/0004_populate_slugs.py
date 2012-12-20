# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        i = 1
        for h in orm.HelpText.objects.all().order_by('title'):
           h.slug = 'slug' + str(i)
           h.order = i
           h.save()
           i = i + 1

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")


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
    symmetrical = True
