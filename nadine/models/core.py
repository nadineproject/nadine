

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
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.utils.encoding import smart_str
from django_localflavor_us.models import USStateField, PhoneNumberField
from django.utils.timezone import localtime, now
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.contrib.sites.models import Site

logger = logging.getLogger(__name__)


GENDER_CHOICES = (
    ('U', 'Not recorded'),
    ('M', 'Man'),
    ('F', 'Woman'),
    ('O', 'Something else'),
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
    url_type = models.ForeignKey(URLType, on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.url

    class Meta:
        app_label = 'nadine'


# TODO - Not quite ready yet --JLS
# def doc_upload_path(instance, filename):
#     ''' Renames an uploaded file based on name given, not on the filename uploaded '''
#     path='.'
#     inst_name = instance.name
#     doc_count = Documents.objects.filter(name=inst_name).count() + 1
#     name = inst_name + str(doc_count)
#     filename='documents/%s.png' % name
#
#     return os.path.join(path, filename)
#
# class Documents(models.Model):
#     name = models.CharField(max_length=255, blank=False)
#     document = models.FileField(upload_to=doc_upload_path)
#
#     def __str__(self):
#         return self.name


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
