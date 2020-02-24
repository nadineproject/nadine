
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import localtime, now

from nadine.models.billing import BillingBatch, UserBill
from nadine.models.membership import Membership

class Command(BaseCommand):
    requires_system_checks = True
    help = "Runs the billing batch."

    # def add_arguments(self, parser):
    #     # Named (optional) arguments
    #     parser.add_argument(
    #         '--delete-open',
    #         action='store_true',
    #         dest='delete-open',
    #         default=False,
    #         help='Delete all open bills',
    #     )
    #     parser.add_argument(
    #         '--start',
    #         default=None,
    #         help='Start date for batch run',
    #     )
    #     parser.add_argument(
    #         '--end',
    #         default=None,
    #         help='End date for batch run',
    #     )

    def handle(self, *args, **options):
        today = localtime(now()).date()

        # print("Examening Open Bills...")
        # open_bills = UserBill.objects.open().order_by('period_start')
        # for bill in open_bills:
        #     for another_bill in open_bills.filter(user=bill.user):
        #         if another_bill != bill:
        #             print("   Combining bills for %s" % bill.user)
        #             bill.combine(another_bill, recalculate=False)
        #             for payment in another_bill.payment_set.all():
        #                 print("   Moving payments to new bill")
        #                 payment.bill = bill
        #                 payment.save()

        # Delete open bills - SHOULD'T BE ANY!
        open_bills = UserBill.objects.open().order_by('period_start')
        for bill in open_bills:
            print("Deleting %s" % bill)
            if bill.payment_set.count() > 0:
                print("  WARNING!  Bill has payments!")
            bill.delete()

        print("Starting our Billing Batch...")
        batch = BillingBatch.objects.create()

        # Run just our subscriptions.  This will create all the new bills for existing members
        batch.run_subscriptions(today)

        # Move any payments from the last migrated bill to our new bill
        print("Migrating Payments...")
        for bill in batch.bills.all():
            for another_bill in UserBill.objects.filter(user=bill.user, period_start=bill.period_start, period_end=bill.period_end):
                if another_bill != bill:
                    print("   Found matching bill for %s %s to %s" % (bill.user.username, bill.period_start, bill.period_end))
                    for payment in another_bill.payment_set.all():
                        print("      Moving payments to new bill")
                        payment.bill = bill
                        payment.save()
                    another_bill.delete()

        # Now run the full batch which will collect all the coworking days, and close bills as needed
        batch.run()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
