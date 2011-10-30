import traceback
from datetime import datetime, date, timedelta

from django.core.exceptions import ObjectDoesNotExist

from front.scheduler import Task, ONE_DAY_SECONDS, ONE_HOUR_SECONDS

class BillingTask(Task):
	"""
	A recurring task which calculates billing.
	The task runs once an hour, but will only run billing once every 24 hours.
	"""
	def __init__(self, loopdelay=ONE_HOUR_SECONDS, initdelay=1):
		Task.__init__(self, self.perform_task, loopdelay, initdelay)
		self.name = "BillingRunTask"

	def perform_task(self):
		from staff import billing
		from staff.models import BillingLog
		try:
			latest_billing_log = BillingLog.objects.latest()
			if latest_billing_log.started > datetime.now() - timedelta(hours=24): return
		except ObjectDoesNotExist:
			pass
		billing.run_billing()		

class MailingListTask(Task):
	"""A recurring task which checks for members who need to be unsubscribed from mailing lists"""
	def __init__(self, loopdelay=3600, initdelay=5):
		Task.__init__(self, self.perform_task, loopdelay, initdelay)
		self.name = "MailingListTask"

	def perform_task(self):
		from staff.models import Member
		Member.objects.unsubscribe_recent_dropouts()      

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
