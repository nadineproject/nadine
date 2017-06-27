from __future__ import print_function
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import localtime, now
from django.db.models import Sum

from nadine.models.membership import Membership
from nadine.models.billing import BillingBatch, UserBill


class Command(BaseCommand):
    requires_system_checks = True
    help = "Runs the billing batch."

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--start',
            default=None,
            help='Start date for batch run',
        )
        parser.add_argument(
            '--end',
            default=None,
            help='End date for batch run',
        )

    def handle(self, *args, **options):
        today = localtime(now()).date()
        yesterday = today - timedelta(days=1)

        start_date = None
        if options['start']:
            start_date = datetime.strptime(options['start'], "%Y-%m-%d").date()

        end_date = None
        if options['end']:
            end_date = datetime.strptime(options['end'], "%Y-%m-%d").date()

        print("Running Billing Batch...")
        BillingBatch.objects.run(start_date, end_date)


# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
