import os
import time
import csv
import ConfigParser

from django.template.defaultfilters import slugify
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from nadine.models import *

PROMPT = '> '

class Command(BaseCommand):
    help = "Sets all user passwords to an empty string"
    requires_system_checks = True

    def handle(self, **options):
        print("Are you you want to blank all the passwords? (y, N)")
        sure = raw_input(PROMPT).strip().lower()
        if sure == "y":
            print("Blanking passwords...")
            for u in User.objects.all():
                u.set_password('')
                u.save()
            print("Done!")
        else:
            print("Exiting!")
