import os
import time
import csv
import configparser

from django.template.defaultfilters import slugify
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from nadine.models import *
from taggit.models import *

class Command(BaseCommand):
    help = "Clean all the tags"
    def handle(self, *args, **options):
        print("Cleaning all the tags...")
        for tag in Tag.objects.all():
            clean = tag.name.strip().lower()
            if tag.name != clean:
                print(("Found '%s'" % tag.name))
                for user in User.objects.filter(profile__tags__name__in=[tag.name]):
                    print(("   Updating '%s'" % user.username))
                    user.profile.tags.add(clean)
                print(("Deleting '%s'" % tag.name))
                tag.delete()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
