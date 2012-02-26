# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'UserDevice'
        db.create_table('arpwatch_userdevice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('device_name', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('mac_address', self.gf('django.db.models.fields.CharField')(unique=True, max_length=17)),
            ('ignore', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('arpwatch', ['UserDevice'])

        # Adding model 'ArpLog'
        db.create_table('arpwatch_arplog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('runtime', self.gf('django.db.models.fields.DateTimeField')()),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['arpwatch.UserDevice'])),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
        ))
        db.send_create_signal('arpwatch', ['ArpLog'])

        # Adding model 'UploadLog'
        db.create_table('arpwatch_uploadlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('loadtime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('file_size', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('arpwatch', ['UploadLog'])


    def backwards(self, orm):
        
        # Deleting model 'UserDevice'
        db.delete_table('arpwatch_userdevice')

        # Deleting model 'ArpLog'
        db.delete_table('arpwatch_arplog')

        # Deleting model 'UploadLog'
        db.delete_table('arpwatch_uploadlog')


    models = {
        'arpwatch.arplog': {
            'Meta': {'ordering': "['-runtime']", 'object_name': 'ArpLog'},
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['arpwatch.UserDevice']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'runtime': ('django.db.models.fields.DateTimeField', [], {})
        },
        'arpwatch.uploadlog': {
            'Meta': {'object_name': 'UploadLog'},
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'file_size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loadtime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'arpwatch.userdevice': {
            'Meta': {'object_name': 'UserDevice'},
            'device_name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mac_address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '17'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['arpwatch']
