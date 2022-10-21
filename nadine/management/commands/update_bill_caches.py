
import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from nadine.models.billing import UserBill


class Command(BaseCommand):
    help = "Updates the cached totals of all UserBill objects"

    def handle(self, *args, **options):
        cnt = UserBill.objects.all().count()
        print("Updating UserBill caches (%d)" % cnt, end='')

        for bill in UserBill.objects.all():
            bill.update_cached_totals()
            print('.', end='')
            sys.stdout.flush()
        print()


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

