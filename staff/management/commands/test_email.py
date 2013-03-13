import os
import time
import urllib
import sys
import datetime

import staff.email
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = "Sends system emails to show everything is working."
	args = "[username]"
	requires_model_validation = False

	def handle(self, *labels, **options):
		if not labels or len(labels) != 1: raise CommandError('Enter a username')
		user = None
		try:
			user = User.objects.get(username=labels[0])
		except:
			raise CommandError("Invalid username '%s'" % labels[0])
			
		print("Sending emails to %s" % user.email)

		staff.email.send_first_day_checkin(user)

# Copyright 2011 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
