import os
import re
import time
import random
import logging
import traceback
import unicodedata
from datetime import datetime, timedelta, date

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.db.models import signals
from django.core.mail import send_mail
from django.dispatch import dispatcher
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.encoding import force_unicode
from django.template.loader import render_to_string

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
