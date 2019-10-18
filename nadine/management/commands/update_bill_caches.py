
import sys
from datetime import datetime

from django.core.management.base import BaseCommand

from nadine.models.billing import UserBill


class Command(BaseCommand):
    requires_system_checks = True
    help = "Updates the cached totals of all UserBill objects"

    def handle(self, *args, **options):
        cnt = UserBill.objects.all().count()
        print(f"Updating UserBill caches ({cnt})", end='')

        for bill in UserBill.objects.all():
            bill.update_cached_totals()
            print('.', end='')
            sys.stdout.flush()
        print()


# Copyright 2019 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
