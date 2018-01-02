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
