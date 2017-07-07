from __future__ import print_function
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

        # Delete all the open  bills
        print("Deleting Open Bills...")
        open_bills = UserBill.objects.open().order_by('period_start')
        for bill in open_bills:
            print("Deleting %s" % bill)
            if bill.payment_set.count() > 0:
                print("  WARNING!  Bill has payments!")
            bill.delete()

        print("Running Batch...")
        batch = BillingBatch.objects.run()
        print("   Ran %d Bills" % batch.bills.count())

        for bill in batch.bills.all():
            for another_bill  in UserBill.objects.filter(user=bill.user, period_start=bill.period_start, period_end=bill.period_end):
                if another_bill != bill:
                    print("Found matching bill for %s %s to %s" % (bill.user.username, bill.period_start, bill.period_end))
                    for payment in another_bill.payment_set.all():
                        print("   Moving payments to new bill")
                        payment.bill = bill
                        payment.save()
                    another_bill.delete()

        # Go through all the active memberships and combine bills if we need to
        # for membership in Membership.objects.active_individual_memberships(today):
        #     user = membership.individualmembership.user
        #     print("  Migrating %s" % user.username)
        #     last_bill = user.bills.last()
        #     if last_bill:
        #         for another_bill in UserBill.objects.filter(user=last_bill.user, period_start=last_bill.period_start, period_end=last_bill.period_end):
        #             if another_bill != last_bill:
        #                 print("    Combining Bill %s and %s" % (another_bill.id, last_bill.id))
        #                 last_bill.combine(another_bill)
        #         if last_bill.period_end < today:
        #             last_bill.closed_ts = None
        #             last_bill.save()




# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
