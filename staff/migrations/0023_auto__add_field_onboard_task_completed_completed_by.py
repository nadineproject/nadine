# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Onboard_Task_Completed.completed_by'
        db.add_column(u'staff_onboard_task_completed', 'completed_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Onboard_Task_Completed.completed_by'
        db.delete_column(u'staff_onboard_task_completed', 'completed_by_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'staff.bill': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Bill'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'created': ('django.db.models.fields.DateField', [], {}),
            'dropins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'bills'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['staff.DailyLog']"}),
            'guest_dropins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guest_bills'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['staff.DailyLog']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bills'", 'to': u"orm['staff.Member']"}),
            'membership': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Membership']", 'null': 'True', 'blank': 'True'}),
            'new_member_deposit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'paid_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'guest_bills'", 'null': 'True', 'to': u"orm['staff.Member']"})
        },
        u'staff.billinglog': {
            'Meta': {'ordering': "['-started']", 'object_name': 'BillingLog'},
            'ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'successful': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'staff.dailylog': {
            'Meta': {'ordering': "['-visit_date', '-created']", 'object_name': 'DailyLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 6, 16, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'guest_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'guest_of'", 'null': 'True', 'to': u"orm['staff.Member']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'daily_logs'", 'to': u"orm['staff.Member']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': "'True'"}),
            'payment': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'visit_date': ('django.db.models.fields.DateField', [], {})
        },
        u'staff.exittask': {
            'Meta': {'ordering': "['order']", 'object_name': 'ExitTask'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'has_desk_only': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'staff.exittaskcompleted': {
            'Meta': {'object_name': 'ExitTaskCompleted'},
            'completed_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.ExitTask']"})
        },
        u'staff.howheard': {
            'Meta': {'ordering': "['name']", 'object_name': 'HowHeard'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'staff.industry': {
            'Meta': {'ordering': "['name']", 'object_name': 'Industry'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'staff.member': {
            'Meta': {'ordering': "['user__first_name', 'user__last_name']", 'object_name': 'Member'},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'email2': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "'U'", 'max_length': '1'}),
            'has_kids': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'howHeard': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.HowHeard']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'industry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Industry']", 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'neighborhood': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Neighborhood']", 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'phone': ('django_localflavor_us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'phone2': ('django_localflavor_us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'promised_followup': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'self_employed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'url_aboutme': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_biznik': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_facebook': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_github': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_linkedin': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_personal': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_professional': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'url_twitter': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'valid_billing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'})
        },
        u'staff.membership': {
            'Meta': {'ordering': "['start_date']", 'object_name': 'Membership'},
            'daily_rate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'dropin_allowance': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'end_date': ('django.db.models.fields.DateField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'guest_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'monthly_guests'", 'null': 'True', 'to': u"orm['staff.Member']"}),
            'has_desk': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_key': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_mail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'memberships'", 'to': u"orm['staff.Member']"}),
            'membership_plan': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.MembershipPlan']", 'null': 'True'}),
            'monthly_rate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'db_index': 'True'})
        },
        u'staff.membershipplan': {
            'Meta': {'object_name': 'MembershipPlan'},
            'daily_rate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'dropin_allowance': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'has_desk': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monthly_rate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        u'staff.neighborhood': {
            'Meta': {'ordering': "['name']", 'object_name': 'Neighborhood'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'staff.onboard_task': {
            'Meta': {'ordering': "['order']", 'object_name': 'Onboard_Task'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'has_desk_only': ('django.db.models.fields.BooleanField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'staff.onboard_task_completed': {
            'Meta': {'unique_together': "(('member', 'task'),)", 'object_name': 'Onboard_Task_Completed'},
            'completed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'completed_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Onboard_Task']"})
        },
        u'staff.securitydeposit': {
            'Meta': {'object_name': 'SecurityDeposit'},
            'amount': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'received_date': ('django.db.models.fields.DateField', [], {}),
            'returned_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'staff.sentemaillog': {
            'Meta': {'object_name': 'SentEmailLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']", 'null': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'success': ('django.db.models.fields.NullBooleanField', [], {'default': 'False', 'null': 'True', 'blank': 'True'})
        },
        u'staff.specialday': {
            'Meta': {'object_name': 'SpecialDay'},
            'day': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']"}),
            'month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'staff.transaction': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Transaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'transactions'", 'symmetrical': 'False', 'to': u"orm['staff.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['staff.Member']"}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '10'})
        }
    }

    complete_apps = ['staff']