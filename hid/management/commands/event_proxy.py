import os
import time
import urllib
import sys
import requests

from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.servers.basehttp import WSGIRequestHandler, run

class SimpleHandler(WSGIRequestHandler, object):

    def __init__(self, *args, **kwargs):
        super(WSGIRequestHandler, self).__init__(*args, **kwargs)

    def handle(self):
        print "self"

class Command(BaseCommand):
    help = "Generate a new encryption key"
    args = ""
    requires_system_checks = False

    def handle(self, *labels, **options):
        run("127.0.0.1", 8000, SimpleHandler)
