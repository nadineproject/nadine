import os
import sys
import time
import urllib.request, urllib.parse, urllib.error
import logging
import datetime

logger = logging.getLogger()

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from interlink.models import unsubscribe_recent_dropouts


class Command(BaseCommand):
    help = "Check for members who need to be unsubscribed from mailing lists"

    def handle(self, *labels, **options):
        unsubscribe_recent_dropouts()


# Copyright 2020 Office Nomads LLC (https://officenomads.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
