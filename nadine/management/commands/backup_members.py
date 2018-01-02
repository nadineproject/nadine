import os
import time
import urllib.request, urllib.parse, urllib.error
import sys
import datetime

from django.core.management.base import BaseCommand, CommandError
from nadine.utils.backup import BackupManager

class Command(BaseCommand):
    help = "Export a CSV of active members"
    args = ""
    requires_system_checks = False

    def handle(self, *args, **options):
        manager = BackupManager()
        manager.export_active_users()
