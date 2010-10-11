import os
import time
import csv
import ConfigParser

from django.template.defaultfilters import slugify
from django.core.management.base import NoArgsCommand, CommandError
from django.core.files import File

from staff import billing

class Command(NoArgsCommand):
   help = "Runs the billing calculator."

   requires_model_validation = True

   def handle_noargs(self, **options):
      billing.run_billing()		

# Copyright 2010 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
