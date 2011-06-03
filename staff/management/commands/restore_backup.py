import os
import time
import urllib
import datetime
import sys

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from staff.backup import BackupManager

class Command(BaseCommand):
	help = "Deletes and then restores the DB and non-static media from a backup created using the make_backup management command."
	args = "[backup_file_path]"
	requires_model_validation = False

	def handle(self, *labels, **options):
		if not labels or len(labels) != 1: raise CommandError('Enter one argument, the path to the backup tar file.')
		manager = BackupManager()
		manager.restore_backup(labels[0])
		
# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
