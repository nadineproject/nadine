import os
import time
import urllib
import sys
import datetime
import json

from nadine.models.membership import Membership
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from collections import OrderedDict

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

        user_data = []
        for user in User.objects.all().order_by('id'):
            data = OrderedDict()
            data['user_id'] = user.id
            data['gender'] = user.profile.gender
            data['howheard'] = str(user.profile.howHeard)
            data['neighborhood'] = str(user.profile.neighborhood)
            data['industry'] = str(user.profile.industry)
            data['has_kids'] = user.profile.has_kids
            data['self_employed'] = user.profile.self_employed
            data['first_visit'] = user.profile.first_visit()
            data['coworking_days'] = user.profile.activity().count()
            data['billable_days'] = user.profile.paid_count()
            data['hosted_days'] = user.profile.hosted_days().count()
            data['has_photo'] = str(user.profile.photo) != ''
            data['emails'] = len(user.profile.all_emails())
            data['files'] = len(user.profile.file_uploads())
            data['websites'] = user.profile.websites.count()
            data['tags'] = []
            for tag in user.profile.tags.all():
                data['tags'].append(str(tag))
            data['memberships'] = []
            for m in Membership.objects.filter(user=user).order_by('start_date'):
                m_data = OrderedDict()
                m_data['plan'] = m.membership_plan.name
                m_data['start_date'] = m.start_date
                m_data['end_date'] = m.end_date
                m_data['monthly_rate'] = m.monthly_rate
                data['memberships'].append(m_data)
            user_data.append(data)

        print("Writing JSON data to: %s" % output)
        with open(output, 'w') as outfile:
            json.dump(user_data, outfile, default=date_handler)



# Copyright 2017 Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
