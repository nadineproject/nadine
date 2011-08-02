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
from django.dispatch import dispatcher
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.encoding import force_unicode
from django.template.loader import render_to_string
from django.core.mail import send_mail, send_mass_mail

class MailingListManager(models.Manager):
   def fetch_all_mail(self):
      """Fetches mail for all mailing lists and returns an array of mailing_lists which reported failures"""
      failures = []
      for mailing_list in self.all():
         if not mailing_list.fetch_mail():
            failures.append(mailing_list)
      return failures

class MailingList(models.Model):
   """Represents both the user facing information about a mailing list and how to fetch the mail"""
   name = models.CharField(max_length=1024)
   description = models.TextField(blank=True)
   subject_prefix = models.CharField(max_length=1024, blank=True)
   
   is_opt_out = models.BooleanField(default=False, help_text='True if new users should be automatically enrolled')

   email_address = models.EmailField()
   
   username = models.CharField(max_length=1024)
   password = models.CharField(max_length=1024)

   pop_host = models.CharField(max_length=1024)
   pop_port = models.IntegerField(default=995)
   smtp_host = models.CharField(max_length=1024)
   smtp_port = models.IntegerField(default=587)

   subscribers = models.ManyToManyField(User, blank=True, related_name='subscribed_mailing_lists')
   moderators = models.ManyToManyField(User, blank=True, related_name='moderated_mailing_lists', help_text='Users who will be sent moderation emails')
   
   objects = MailingListManager()
   
   def fetch_mail(self):
      """Fetches mailing and returns True if successful and False if it failed"""
      from interlink import DEFAULT_MAIL_CHECKER
      checker = DEFAULT_MAIL_CHECKER(self)
      try:
         checker.fetch_mail()
         return True
      except:
         traceback.print_exc()
         return False

   @property
   def moderator_addresses(self):
      """Returns a tuple of email address strings, one for each moderator address"""
      return tuple([moderator.email for moderator in self.moderators.all()])

   @property
   def subscriber_addresses(self):
      """Returns a tuple of email address strings, one for each subscribed address"""
      return tuple([sub.email for sub in self.subscribers.all()])
   
   def __unicode__(self): return '%s: %i' % (self.name, self.id)
   
class IncomingMail(models.Model):
   """An email as popped for a mailing list"""
   mailing_list = models.ForeignKey(MailingList, related_name='incoming_mails')
   origin_address = models.EmailField()
   sent_time = models.DateTimeField()
   subject = models.TextField(blank=True)
   body = models.TextField(blank=True)

   STATES = (('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject'))
   state = models.CharField(max_length=10, choices=STATES, default='raw')

   created = models.DateTimeField(auto_now_add=True)

   def __unicode__(self): return '%s: %s' % (self.origin_address, self.subject)

class OutgoingMail(models.Model):
   """Emails which are consumed by the front.tasks.EmailTask"""
   mailing_list = models.ForeignKey(MailingList, related_name='outgoing_mails')
   original_mail = models.ForeignKey(IncomingMail, blank=True, help_text='The incoming mail which caused this mail to be sent')
   subject = models.TextField(blank=True)
   body = models.TextField(blank=True)

   attempts = models.IntegerField(blank=False, null=False, default=0)
   last_attempt = models.DateTimeField(blank=True, null=True)
   sent = models.DateTimeField(blank=True, null=True)

   created = models.DateTimeField(auto_now_add=True)

   def send(self):
      if self.sent: return False
      self.last_attempt = datetime.now()
      self.attempts = self.attempts + 1
      self.save()
      try:
         if self.mailing_list.subject_prefix:
            sub = '[%s] %s' % (self.mailing_list.subject_prefix, self.subject)
         else:
            sub = self.subject
         send_mass_mail((sub, self.body, self.mailing_list.email_address, self.mailing_list.subscriber_addresses))
         self.sent = datetime.now()
         self.save()
         return True
      except:
         traceback.print_exc()
         return False

   class Meta:
      verbose_name_plural = 'outgoing mails'

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
