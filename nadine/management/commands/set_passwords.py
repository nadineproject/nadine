import os
import time
import csv
import configparser

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

PROMPT = '> '

class Command(BaseCommand):
    help = "Sets all user passwords."
    def handle(self, *args, **options):
        print("What would you like to set all the passwords to?")
        passwd = input(PROMPT).strip()
        if len(passwd) == 0:
            print("Exiting!")
        else:
            print("Are you you want to set all the passwords? (y, N)")
            sure = input(PROMPT).strip().lower()
            if sure == "y":
                print("Setting passwords...")
                for u in User.objects.all():
                    u.set_password(passwd)
                    u.save()
                print("Done!")
            else:
                print("Exiting!")


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
