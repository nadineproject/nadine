
from datetime import datetime

from django.core.management.base import BaseCommand

from nadine.models.billing import BillingBatch, UserBill


class Command(BaseCommand):
    requires_system_checks = True
    help = "Runs the billing batch."

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--delete-open',
            action='store_true',
            dest='delete-open',
            default=False,
            help='Delete all open bills',
        )
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
        start_date = end_date = None
        if options['delete-open']:
            open_bills = UserBill.objects.open().order_by('period_start')
            if open_bills:
                print("Deleting Open Bills...")
                start_date = open_bills.first().period_start
                for bill in open_bills:
                    print("Deleting %s" % bill)
                    bill.delete()

        if options['start']:
            start_date = datetime.strptime(options['start'], "%Y-%m-%d").date()

        if options['end']:
            end_date = datetime.strptime(options['end'], "%Y-%m-%d").date()

        print("Running Batch: start=%s end=%s" % (start_date, end_date))
        batch = BillingBatch.objects.run(start_date, end_date)
        print("%d Bills" % batch.bills.count())


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
