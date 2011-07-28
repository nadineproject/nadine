# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MailingList'
        db.create_table('interlink_mailinglist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('subject_prefix', self.gf('django.db.models.fields.CharField')(max_length=1024, blank=True)),
            ('is_opt_out', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email_address', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('pop_host', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('pop_port', self.gf('django.db.models.fields.IntegerField')(default=995)),
            ('smtp_host', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('smtp_port', self.gf('django.db.models.fields.IntegerField')(default=587)),
        ))
        db.send_create_signal('interlink', ['MailingList'])

        # Adding M2M table for field subscribers on 'MailingList'
        db.create_table('interlink_mailinglist_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['interlink.mailinglist'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('interlink_mailinglist_subscribers', ['mailinglist_id', 'user_id'])

        # Adding M2M table for field moderators on 'MailingList'
        db.create_table('interlink_mailinglist_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mailinglist', models.ForeignKey(orm['interlink.mailinglist'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('interlink_mailinglist_moderators', ['mailinglist_id', 'user_id'])

        # Adding model 'IncomingMail'
        db.create_table('interlink_incomingmail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailing_list', self.gf('django.db.models.fields.related.ForeignKey')(related_name='incoming_mails', to=orm['interlink.MailingList'])),
            ('origin_address', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('subject', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('interlink', ['IncomingMail'])

        # Adding model 'OutgoingMail'
        db.create_table('interlink_outgoingmail', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mailing_list', self.gf('django.db.models.fields.related.ForeignKey')(related_name='outgoing_mails', to=orm['interlink.MailingList'])),
            ('original_mail', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['interlink.IncomingMail'], blank=True)),
            ('subject', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('last_attempt', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('interlink', ['OutgoingMail'])


    def backwards(self, orm):
        
        # Deleting model 'MailingList'
        db.delete_table('interlink_mailinglist')

        # Removing M2M table for field subscribers on 'MailingList'
        db.delete_table('interlink_mailinglist_subscribers')

        # Removing M2M table for field moderators on 'MailingList'
        db.delete_table('interlink_mailinglist_moderators')

        # Deleting model 'IncomingMail'
        db.delete_table('interlink_incomingmail')

        # Deleting model 'OutgoingMail'
        db.delete_table('interlink_outgoingmail')


    models = {
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
        },
        'interlink.incomingmail': {
            'Meta': {'object_name': 'IncomingMail'},
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailing_list': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'incoming_mails'", 'to': "orm['interlink.MailingList']"}),
            'origin_address': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'subject': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'interlink.mailinglist': {
            'Meta': {'object_name': 'MailingList'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email_address': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_opt_out': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'moderated_mailing_lists'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'pop_host': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'pop_port': ('django.db.models.fields.IntegerField', [], {'default': '995'}),
            'smtp_host': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'smtp_port': ('django.db.models.fields.IntegerField', [], {'default': '587'}),
            'subject_prefix': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'blank': 'True'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subscribed_mailing_lists'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'interlink.outgoingmail': {
            'Meta': {'object_name': 'OutgoingMail'},
            'attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_attempt': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mailing_list': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'outgoing_mails'", 'to': "orm['interlink.MailingList']"}),
            'original_mail': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['interlink.IncomingMail']", 'blank': 'True'}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['interlink']
