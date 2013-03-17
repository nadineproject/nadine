import os
import time
import urllib
import sys
import datetime

import staff.email
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = "Sends system emails to given user."
	args = "[username] [message]"
	requires_model_validation = False

	def handle(self, *labels, **options):
		if not labels or len(labels) != 2: raise CommandError('Enter a username and message to send')
		
		# Make sure we have a valid user
		user = None
		try:
			user = User.objects.get(username=labels[0])
		except:
			raise CommandError("Invalid username '%s'" % labels[0])
		
		message = labels[1].lower()
		valid_message = False
		if message == "introduction" or message == "all":
			print("Sending introduction...")
			staff.email.send_introduction(user)
			valid_message = True
		if message == "newsletter" or message == "all":
			print("Sending newsletter...")
			staff.email.subscribe_to_newsletter(user)
			valid_message = True
		if message == "new_member" or message == "all":
			print("Sending new_member...")
			staff.email.send_new_membership(user)
			valid_message = True
		if message == "first_day_checkin" or message == "all":
			print("Sending first_day_checkin...")
			staff.email.send_first_day_checkin(user)
			valid_message = True
		if message == "exit_survey" or message == "all":
			print("Sending exit_survey...")
			staff.email.send_exit_survey(user)
			valid_message = True
		if message == "member_survey" or message == "all":
			print("Sending member_survey...")
			staff.email.send_member_survey(user)
			valid_message = True
		if message == "no_return_checkin" or message == "all":
			print("Sending no_return_checkin...")
			staff.email.send_no_return_checkin(user)
			valid_message = True
		if message == "invalid_billing" or message == "all":
			print("Sending invalid_billing...")
			staff.email.send_invalid_billing(user)
			valid_message = True

		if not valid_message:
			print("Message must be: all, introduction, newsletter, new_membership, first_day_checkin, exit_survey, member_survey, no_return checkin, invalid_billing")
			raise CommandError("Invalid message '%s'" % labels[1])

		print("Email address: %s" % user.email)

# Copyright 2013 Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
