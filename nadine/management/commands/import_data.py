import os
import time
import urllib.request, urllib.parse, urllib.error
import sys
import datetime

from django.apps import apps, AppConfig

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from nadine.models import *

class Command(BaseCommand):
    help = "Import Data File"
    args = "[model] [file_name]"

    def handle(self, *args, **options):
        if not args or len(args) != 2:
            raise CommandError('Usage:  <model> <file_name>')
        model_name = args[0]
        file_name = args[1]

        # Grab our model
        Model = apps.get_model('nadine', model_name)
        print(("Row Count Before Import: %d" % Model.objects.count()))

        with open(file_name) as f:
            for line in f:
                name = line.strip()
                if Model.objects.filter(name=name).count() == 0:
                    Model.objects.create(name=name)
        print(("Row Count After Import: %d" % Model.objects.count()))


# Copyright 2020Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
