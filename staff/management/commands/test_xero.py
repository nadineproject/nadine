import os
import time
import csv
import ConfigParser

from django.template.defaultfilters import slugify
from django.core.management.base import NoArgsCommand, CommandError
from django.core.files import File

from nadine import xero_api

class Command(NoArgsCommand):
    help = "Tests the xero connection."

    requires_system_checks = True

    def handle_noargs(self, **options):
        if xero_api.test_xero_connection():
            print "Xero connection is working properly"
        else:
            print "Xero connection isn't working!"