import os
import time
import urllib
import sys
import datetime

from nadine import email
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sends system emails to given user."
    args = "[username] [message]"
    requires_system_checks = False

    def print_keys(self):
        print("Valid Message Keys: ")
        for key in email.valid_message_keys():
            print("   " + key)

    def handle(self, *labels, **options):
        if not labels or len(labels) != 2:
            self.print_keys()
            raise CommandError('Enter a username and message key')

        # Make sure we have a valid user
        user = None
        try:
            user = User.objects.get(username=labels[0])
        except:
            raise CommandError("Invalid username '%s'" % labels[0])

        message = labels[1].lower()
        print("Sending %s..." % message)
        if not email.send_manual(user, message):
            self.print_keys()
            raise CommandError("Invalid message key '%s'" % labels[1])

        print("Email address: %s" % user.email)

# Copyright 2013 Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
