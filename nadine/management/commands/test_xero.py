import os
import time
import csv

from django.template.defaultfilters import slugify
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from nadine.utils import xero_api

class Command(BaseCommand):
    help = "Tests the xero connection."

    requires_system_checks = True

    def handle(self, *args, **options):
        if xero_api.test_xero_connection():
            print("Xero connection is working properly")
        else:
            print("Xero connection isn't working!")


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
