from __future__ import print_function

from django.core.management.base import BaseCommand, CommandError

from nadine.models.membership import Membership
from nadine.models.billing import UserBill


def generate(membership):
    print("  %s: %s" % (membership.who, membership.package_name()))
    bill_dict = membership.generate_bill()
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
            '--regenerate-open-bills',
            action='store_true',
            dest='regenerate-open-bills',
            default=False,
            help='Regenerate all open bills',
        )

    def handle(self, *args, **options):
        if options['regenerate-open-bills']:
            print("Regenerationg Open Bills...")
            for bill in UserBill.objects.unpaid():
                if bill.membership:
                    generate(bill.membership)

        print("Generating Bills Ready for Billing...")
        for membership in Membership.objects.ready_for_billing():
            generate(membership)

# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
