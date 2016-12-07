from __future__ import unicode_literals

import os
import uuid
import pprint
import traceback
import operator
import logging
import hashlib
from random import random
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.encoding import smart_str
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


GENDER_CHOICES = (
    ('U', 'Unknown'),
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)


class HowHeard(models.Model):

    """A record of how a person discovered the space"""
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class Industry(models.Model):

    """The type of work a user does"""
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        ordering = ['name']


class Neighborhood(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class URLType(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self): return self.name

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class Website(models.Model):
    url_type = models.ForeignKey(URLType)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.url

    class Meta:
        app_label = 'nadine'


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
