from __future__ import print_function
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import localtime, now
from django.db.models import Sum

from nadine.models.membership import Membership
from nadine.models.billing import UserBill


def generate(membership):
    print("  %s: %s" % (membership.who, membership.package_name()))
    bill_dict = membership.generate_bills()
    if bill_dict:
        for payer, row in bill_dict.items():
            bill = row['bill']
            print("    BillID: %s, Payer: %s, Amount: $%s" % (bill.id, payer, bill.amount))
    else:
        print("    No bill")


class Command(BaseCommand):
    requires_system_checks = True
    help = "Runs the billing calculator."

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
            '--regenerate',
            action='store_true',
            dest='regenerate',
            default=False,
            help='Regenerate all open bills',
        )
        parser.add_argument(
            '--retroactive',
            action='store_true',
            dest='retroactive',
            default=False,
            help='Retroactivly generate bills',
        )
    def handle(self, *args, **options):
        today = localtime(now()).date()
        yesterday = today - timedelta(days=1)

        # Optionally delete all open bills
        if options['delete-open']:
            print("Deleting Open Bills...")
            for bill in UserBill.objects.unpaid():
                print("Deleting bill %s" % bill.id)
                bill.delete()

        # Grab the date of our last, non zero bill
        last_bill_date = UserBill.objects.non_zero().filter(due_date__lt=today).order_by('due_date').last().due_date
        print("Last Bill Date: %s" % last_bill_date)

        # Optionally regenerate all open bills
        if options['regenerate']:
            print("Regenerationg Open Bills...")
            for bill in UserBill.objects.unpaid():
                if bill.membership:
                    generate(bill.membership)

        # Generate all the bills for today
        print("Generating Bills Ready for Billing Today...")
        for membership in Membership.objects.ready_for_billing():
            generate(membership)

        # Optionally geneate back to our last_bill_date
        if options['retroactive']:
            print("Retroactivly Generating Bills...")
            target_date = yesterday
            while target_date > last_bill_date:
                print("Generating Bills on %s..." % target_date)
                for membership in Membership.objects.ready_for_billing(target_date):
                    generate(membership)
                target_date = target_date - timedelta(days=1)


# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
