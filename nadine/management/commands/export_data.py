import os
import time
import urllib
import sys
import datetime
import json

from nadine.models.membership import Membership
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

def date_handler(x):
    if isinstance(x, datetime.date):
        return x.isoformat()
    raise TypeError("Unknown type")

class Command(BaseCommand):
    help = "Sends system emails to given user."
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument('output', type=str)

    def handle(self, *labels, **options):
        output = options['output']

        memberships = []
        for m in Membership.objects.all():
            memberships.append({'user_id':m.user.id, 'start_date':m.start_date, 'end_date':m.end_date, 'monthly_rate':m.monthly_rate})

        print("Writing JSON data to: %s" % output)
        with open(output, 'w') as outfile:
            json.dump(memberships, outfile, default=date_handler)



# Copyright 2017 Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
