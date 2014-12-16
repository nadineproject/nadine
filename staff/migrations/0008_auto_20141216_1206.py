# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):

	dependencies = [
		('staff', '0007_auto_20141216_1156'),
	]

	database_operations = [
		migrations.AlterModelTable('Bill', 'nadine_bill'),
		migrations.AlterModelTable('BillingLog', 'nadine_billinglog'),
		migrations.AlterModelTable('DailyLog', 'nadine_dailylog'),
		migrations.AlterModelTable('ExitTask', 'nadine_exittask'),
		migrations.AlterModelTable('ExitTaskCompleted', 'nadine_exittaskcompleted'),
		migrations.AlterModelTable('FileUpload', 'nadine_fileupload'),
		migrations.AlterModelTable('HowHeard', 'nadine_howheard'),
		migrations.AlterModelTable('Industry', 'nadine_industry'),
		migrations.AlterModelTable('Member', 'nadine_member'),
		migrations.AlterModelTable('MemberNote', 'nadine_membernote'),
		migrations.AlterModelTable('Membership', 'nadine_membership'),
		migrations.AlterModelTable('MembershipPlan', 'nadine_membershipplan'),
		migrations.AlterModelTable('Neighborhood', 'nadine_neighborhood'),
		migrations.AlterModelTable('Onboard_Task', 'nadine_onboard_task'),
		migrations.AlterModelTable('Onboard_Task_Completed', 'nadine_onboard_task_completed'),
		migrations.AlterModelTable('SecurityDeposit', 'nadine_securitydeposit'),
		migrations.AlterModelTable('SentEmailLog', 'nadine_sentemaillog'),
		migrations.AlterModelTable('SpecialDay', 'nadine_specialday'),
		migrations.AlterModelTable('Transaction', 'nadine_transaction'),
	]

	state_operations = [
		migrations.DeleteModel('Bill'),
		migrations.DeleteModel('BillingLog'),
		migrations.DeleteModel('DailyLog'),
		migrations.DeleteModel('ExitTask'),
		migrations.DeleteModel('ExitTaskCompleted'),
		migrations.DeleteModel('FileUpload'),
		migrations.DeleteModel('HowHeard'),
		migrations.DeleteModel('Industry'),
		migrations.DeleteModel('Member'),
		migrations.DeleteModel('MemberNote'),
		migrations.DeleteModel('Membership'),
		migrations.DeleteModel('MembershipPlan'),
		migrations.DeleteModel('Neighborhood'),
		migrations.DeleteModel('Onboard_Task'),
		migrations.DeleteModel('Onboard_Task_Completed'),
		migrations.DeleteModel('SecurityDeposit'),
		migrations.DeleteModel('SentEmailLog'),
		migrations.DeleteModel('SpecialDay'),
		migrations.DeleteModel('Transaction'),
	]

	operations = [
		migrations.SeparateDatabaseAndState(database_operations=database_operations, state_operations=state_operations)
	]
