import os
import time
import csv
import ConfigParser

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

PROMPT = '> '

class Command(BaseCommand):
    help = "Sets all user passwords."
    def handle(self, **options):
        print("What would you like to set all the passwords to?")
        passwd = raw_input(PROMPT).strip()
        if len(passwd) == 0:
            print("Exiting!")
        else:
            print("Are you you want to set all the passwords? (y, N)")
            sure = raw_input(PROMPT).strip().lower()
            if sure == "y":
                print("Setting passwords...")
                for u in User.objects.all():
                    u.set_password(passwd)
                    u.save()
                print("Done!")
            else:
                print("Exiting!")
