import os
import time
import urllib.request, urllib.parse, urllib.error
import datetime
import sys

from django.core.management.base import BaseCommand, CommandError

from nadine.utils.backup import BackupManager


class Command(BaseCommand):
    help = "Deletes and then restores the DB and non-static media from a backup created using the make_backup management command."
    args = "[backup_file_path]"

    def add_arguments(self, parser):
        parser.add_argument('backup_file', nargs='+', type=str)

    def handle(self, *args, **options):
        backup_file = options['backup_file'][0]
        manager = BackupManager()
        manager.restore_backup(backup_file)


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

