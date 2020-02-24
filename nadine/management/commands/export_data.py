import os
import time
import urllib.request, urllib.parse, urllib.error
import sys
import datetime
import json

from nadine.models.membership import IndividualMembership, ResourceSubscription
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from collections import OrderedDict

def date_handler(x):
    if isinstance(x, datetime.date):
        return x.isoformat()
    raise TypeError("Unknown type")

class Command(BaseCommand):
    help = "Export user data for analysys"
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument('output', type=str)

    def handle(self, *args, **options):
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
            data['first_visit'] = user.profile.first_visit
            data['coworking_days'] = user.coworkingday_set.all().count()
            data['billable_days'] = user.coworkingday_set.filter(payment='Bill').count()
            data['hosted_days'] = user.profile.hosted_days().count()
            data['has_photo'] = str(user.profile.photo) != ''
            data['emails'] = len(user.profile.all_emails())
            data['files'] = len(user.profile.file_uploads())
            data['websites'] = user.profile.websites.count()
            data['tags'] = []
            for tag in user.profile.tags.all():
                data['tags'].append(str(tag))

            # Pull IndividualMembership ResourceSubscription
            # TODO - Grab OrganizationMemberships too
            data['subscriptions'] = []
            membership = IndividualMembership.objects.get(user=user)
            for s in ResourceSubscription.objects.filter(membership=membership).order_by('start_date'):
                s_data = OrderedDict()
                s_data['package'] = s.package_name
                s_data['start_date'] = s.start_date
                s_data['end_date'] = s.end_date
                s_data['monthly_rate'] = str(s.monthly_rate)
                data['subscriptions'].append(s_data)
            user_data.append(data)

        print(user_data)

        print(("Writing JSON data to: %s" % output))
        with open(output, 'w') as outfile:
            json.dump(user_data, outfile, default=date_handler)



# Copyright 2020Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
