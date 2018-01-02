import os
import time
import csv
import configparser

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
