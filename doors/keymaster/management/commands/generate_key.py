import os
import time
import urllib.request, urllib.parse, urllib.error
import sys
import requests

from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from cryptography.fernet import Fernet

class Command(BaseCommand):
    help = "Generate a new encryption key"
    args = ""
    requires_system_checks = False

    def handle(self, *labels, **options):
        print((Fernet.generate_key()))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
