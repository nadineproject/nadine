# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BillingLog'
        db.create_table('staff_billinglog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('ended', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('successful', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('staff', ['BillingLog'])

        # Adding model 'Bill'
        db.create_table('staff_bill', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(related_name='bills', to=orm['staff.Member'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=7, decimal_places=2)),
            ('created', self.gf('django.db.models.fields.DateField')()),
            ('monthly_log', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.MonthlyLog'], null=True, blank=True)),
            ('new_member_deposit', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('paid_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='guest_bills', null=True, to=orm['staff.Member'])),
        ))
        db.send_create_signal('staff', ['Bill'])

        # Adding M2M table for field dropins on 'Bill'
        db.create_table('staff_bill_dropins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bill', models.ForeignKey(orm['staff.bill'], null=False)),
            ('dailylog', models.ForeignKey(orm['staff.dailylog'], null=False))
        ))
        db.create_unique('staff_bill_dropins', ['bill_id', 'dailylog_id'])

        # Adding M2M table for field guest_dropins on 'Bill'
        db.create_table('staff_bill_guest_dropins', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bill', models.ForeignKey(orm['staff.bill'], null=False)),
            ('dailylog', models.ForeignKey(orm['staff.dailylog'], null=False))
        ))
        db.create_unique('staff_bill_guest_dropins', ['bill_id', 'dailylog_id'])

        # Adding model 'Transaction'
        db.create_table('staff_transaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Member'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='open', max_length=10)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=7, decimal_places=2)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('staff', ['Transaction'])

        # Adding M2M table for field bills on 'Transaction'
        db.create_table('staff_transaction_bills', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('transaction', models.ForeignKey(orm['staff.transaction'], null=False)),
            ('bill', models.ForeignKey(orm['staff.bill'], null=False))
        ))
        db.create_unique('staff_transaction_bills', ['transaction_id', 'bill_id'])

        # Adding model 'HowHeard'
        db.create_table('staff_howheard', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('staff', ['HowHeard'])

        # Adding model 'Industry'
        db.create_table('staff_industry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('staff', ['Industry'])

        # Adding model 'Neighborhood'
        db.create_table('staff_neighborhood', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('staff', ['Neighborhood'])

        # Adding model 'Member'
        db.create_table('staff_member', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('email2', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('phone', self.gf('django.contrib.localflavor.us.models.PhoneNumberField')(max_length=20, null=True, blank=True)),
            ('phone2', self.gf('django.contrib.localflavor.us.models.PhoneNumberField')(max_length=20, null=True, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('howHeard', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.HowHeard'], null=True, blank=True)),
            ('industry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Industry'], null=True, blank=True)),
            ('neighborhood', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Neighborhood'], null=True, blank=True)),
            ('has_kids', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('self_employed', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('company_name', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('promised_followup', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateField')(auto_now=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('staff', ['Member'])

        # Adding model 'DailyLog'
        db.create_table('staff_dailylog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(related_name='daily_logs', to=orm['staff.Member'])),
            ('visit_date', self.gf('django.db.models.fields.DateField')()),
            ('payment', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('guest_of', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='guest_of', null=True, to=orm['staff.Member'])),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=128, blank='True')),
        ))
        db.send_create_signal('staff', ['DailyLog'])

        # Adding model 'MonthlyLog'
        db.create_table('staff_monthlylog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(related_name='monthly_logs', to=orm['staff.Member'])),
            ('plan', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('start_date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('rate', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('guest_dropins', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('guest_of', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='monthly_guests', null=True, to=orm['staff.Member'])),
        ))
        db.send_create_signal('staff', ['MonthlyLog'])

        # Adding model 'ExitTask'
        db.create_table('staff_exittask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('order', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('staff', ['ExitTask'])

        # Adding model 'ExitTaskCompleted'
        db.create_table('staff_exittaskcompleted', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Member'])),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.ExitTask'])),
            ('completed_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('staff', ['ExitTaskCompleted'])

        # Adding model 'Onboard_Task'
        db.create_table('staff_onboard_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('order', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('monthly_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('staff', ['Onboard_Task'])

        # Adding model 'Onboard_Task_Completed'
        db.create_table('staff_onboard_task_completed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Member'])),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['staff.Onboard_Task'])),
            ('completed_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('staff', ['Onboard_Task_Completed'])

        # Adding unique constraint on 'Onboard_Task_Completed', fields ['member', 'task']
        db.create_unique('staff_onboard_task_completed', ['member_id', 'task_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Onboard_Task_Completed', fields ['member', 'task']
        db.delete_unique('staff_onboard_task_completed', ['member_id', 'task_id'])

        # Deleting model 'BillingLog'
        db.delete_table('staff_billinglog')

        # Deleting model 'Bill'
        db.delete_table('staff_bill')

        # Removing M2M table for field dropins on 'Bill'
        db.delete_table('staff_bill_dropins')

        # Removing M2M table for field guest_dropins on 'Bill'
        db.delete_table('staff_bill_guest_dropins')

        # Deleting model 'Transaction'
        db.delete_table('staff_transaction')

        # Removing M2M table for field bills on 'Transaction'
        db.delete_table('staff_transaction_bills')

        # Deleting model 'HowHeard'
        db.delete_table('staff_howheard')

        # Deleting model 'Industry'
        db.delete_table('staff_industry')

        # Deleting model 'Neighborhood'
        db.delete_table('staff_neighborhood')

        # Deleting model 'Member'
        db.delete_table('staff_member')

        # Deleting model 'DailyLog'
        db.delete_table('staff_dailylog')

        # Deleting model 'MonthlyLog'
        db.delete_table('staff_monthlylog')

        # Deleting model 'ExitTask'
        db.delete_table('staff_exittask')

        # Deleting model 'ExitTaskCompleted'
        db.delete_table('staff_exittaskcompleted')

        # Deleting model 'Onboard_Task'
        db.delete_table('staff_onboard_task')

        # Deleting model 'Onboard_Task_Completed'
        db.delete_table('staff_onboard_task_completed')


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
        'staff.bill': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Bill'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'created': ('django.db.models.fields.DateField', [], {}),
            'dropins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'bills'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['staff.DailyLog']"}),
            'guest_dropins': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'guest_bills'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['staff.DailyLog']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bills'", 'to': "orm['staff.Member']"}),
            'monthly_log': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.MonthlyLog']", 'null': 'True', 'blank': 'True'}),
            'new_member_deposit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'paid_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'guest_bills'", 'null': 'True', 'to': "orm['staff.Member']"})
        },
        'staff.billinglog': {
            'Meta': {'ordering': "['-started']", 'object_name': 'BillingLog'},
            'ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'successful': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'staff.dailylog': {
            'Meta': {'ordering': "['-visit_date']", 'object_name': 'DailyLog'},
            'guest_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'guest_of'", 'null': 'True', 'to': "orm['staff.Member']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'daily_logs'", 'to': "orm['staff.Member']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': "'True'"}),
            'payment': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'visit_date': ('django.db.models.fields.DateField', [], {})
        },
        'staff.exittask': {
            'Meta': {'ordering': "['order']", 'object_name': 'ExitTask'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'staff.exittaskcompleted': {
            'Meta': {'object_name': 'ExitTaskCompleted'},
            'completed_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Member']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.ExitTask']"})
        },
        'staff.howheard': {
            'Meta': {'ordering': "['name']", 'object_name': 'HowHeard'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'staff.industry': {
            'Meta': {'ordering': "['name']", 'object_name': 'Industry'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'staff.member': {
            'Meta': {'ordering': "['user__first_name', 'user__last_name']", 'object_name': 'Member'},
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'email2': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'has_kids': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'howHeard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.HowHeard']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'industry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Industry']", 'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'neighborhood': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Neighborhood']", 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'phone2': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'promised_followup': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'self_employed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'staff.monthlylog': {
            'Meta': {'ordering': "['start_date']", 'object_name': 'MonthlyLog'},
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'guest_dropins': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'guest_of': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'monthly_guests'", 'null': 'True', 'to': "orm['staff.Member']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'monthly_logs'", 'to': "orm['staff.Member']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'plan': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'rate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start_date': ('django.db.models.fields.DateField', [], {})
        },
        'staff.neighborhood': {
            'Meta': {'ordering': "['name']", 'object_name': 'Neighborhood'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'staff.onboard_task': {
            'Meta': {'ordering': "['order']", 'object_name': 'Onboard_Task'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monthly_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'order': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'staff.onboard_task_completed': {
            'Meta': {'unique_together': "(('member', 'task'),)", 'object_name': 'Onboard_Task_Completed'},
            'completed_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Member']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Onboard_Task']"})
        },
        'staff.transaction': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Transaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '7', 'decimal_places': '2'}),
            'bills': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'transactions'", 'symmetrical': 'False', 'to': "orm['staff.Bill']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['staff.Member']"}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '10'})
        }
    }

    complete_apps = ['staff']
