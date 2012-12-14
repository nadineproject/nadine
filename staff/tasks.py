from celery.task import task

from datetime import datetime, timedelta


@task(ignore_result=True)
def billing_task():
	"""
	A recurring task which calculates billing.
	The task runs once an hour, but will only run billing once every 24 hours.
	"""
	import billing
	from models import BillingLog

	last_day = datetime.now() - timedelta(hours=24)
	if not BillingLog.objects.filter(started__gt=last_day).exists():
		billing.run_billing()

@task(ignore_result=True)
def unsubscribe_recent_dropouts_task():
	"""A recurring task which checks for members who need to be unsubscribed from mailing lists"""
	from models import Member
	Member.objects.unsubscribe_recent_dropouts()

@task(ignore_result=False)
def test_tasks():
	from django.core.mail import send_mail
	send_mail("email test", "this is your message on drugs", settings.EMAIL_ADDRESS, ["jsayles@gmail.com",], fail_silently=False)

@task(ignore_result=False)
def make_backup():
	from staff.backup import BackupManager
	manager = BackupManager()
	manager.make_backup()

# Copyright 2012 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
