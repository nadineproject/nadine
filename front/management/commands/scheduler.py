import os
import time
import urllib
import sys
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from front.scheduler import Scheduler

class Command(BaseCommand):
   help = "Runs the process which schedules Tasks from settings.SCHEDULED_TASKS."
   args = ""
   requires_model_validation = True

   def handle(self, *labels, **options):
      scheduler = Scheduler()
      for task in settings.SCHEDULED_TASKS: scheduler.add_task(task)
      scheduler.start_all_tasks()

# Copyright 2011 Office Nomads LLC, Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
