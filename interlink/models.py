import os
import re
import time
import email
import random
import logging
import smtplib
import traceback
import unicodedata
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.db.models import signals
from django.dispatch import dispatcher
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.utils.encoding import force_unicode
from django.template.loader import render_to_string
from django.core.mail import send_mail, send_mass_mail

from staff.models import Member, Membership

def user_by_email(email):
   users = User.objects.filter(email=email)
   if len(users) > 0: return users[0]
   members = Member.objects.filter(email2=email)
   if len(members) > 0: return members[0]
   return None
User.objects.find_by_email = user_by_email

def membership_save_callback(sender, **kwargs):
	"""When a membership is created, add the user to any opt-out mailing lists"""
	membership = kwargs['instance']
	created = kwargs['created']
	if not created: return 
	mailing_lists = MailingList.objects.filter(is_opt_out=True)
	for ml in mailing_lists: ml.subscribers.add(membership.member.user)
post_save.connect(membership_save_callback, sender=Membership)


def awaiting_moderation(user):
   """Returns an array of IncomingMail objects which await moderation by this user"""
   return IncomingMail.objects.filter(state='moderate').filter(mailing_list__moderators__username=user.username)
User.mail_awaiting_moderation = awaiting_moderation

class MailingListManager(models.Manager):
   def unsubscribe_from_all(self, user):
      for ml in self.all():
         if user in ml.subscribers.all(): ml.subscribers.remove(user)
   
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
   moderator_controlled = models.BooleanField(default=False, help_text='True if only the moderators can send mail to the list and can unsubscribe users.')

   email_address = models.EmailField()
   
   username = models.CharField(max_length=1024)
   password = models.CharField(max_length=1024)

   pop_host = models.CharField(max_length=1024)
   pop_port = models.IntegerField(default=995)
   smtp_host = models.CharField(max_length=1024)
   smtp_port = models.IntegerField(default=587)

   subscribers = models.ManyToManyField(User, blank=True, related_name='subscribed_mailing_lists')
   moderators = models.ManyToManyField(User, blank=True, related_name='moderated_mailing_lists', help_text='Users who will be sent moderation emails', limit_choices_to={'is_staff': True})
   
   objects = MailingListManager()
   
   def fetch_mail(self):
      """Fetches mailing and returns True if successful and False if it failed"""
      from interlink.mail import DEFAULT_MAIL_CHECKER
      checker = DEFAULT_MAIL_CHECKER(self)
      try:
         checker.fetch_mail()
         return True
      except:
         traceback.print_exc()
         return False

   @property
   def list_id(self):
      """Used for List-ID mail headers"""
      return '%s <%s-%s>' % (self.name, Site.objects.get_current().domain, self.id)
      
   @property
   def moderator_addresses(self):
      """Returns a tuple of email address strings, one for each moderator address"""
      return tuple([moderator.email for moderator in self.moderators.all()])

   @property
   def subscriber_addresses(self):
      """Returns a tuple of email address strings, one for each subscribed address"""
      return tuple([sub.email for sub in self.subscribers.all()])
   
   def __unicode__(self): return '%s' % self.name

   @models.permalink
   def get_absolute_url(self): return ('interlink.views.list', (), { 'id':self.id })

def user_mailing_list_memberships(user):
	"""Returns an array of tuples of <MailingList, is_subscriber> for a User"""
	return [(ml, user in ml.subscribers.all()) for ml in MailingList.objects.all()]
User.mailing_list_memberships = user_mailing_list_memberships

class IncomingMailManager(models.Manager):
   def process_incoming(self):
      for incoming in self.filter(state='raw'):
         incoming.owner = User.objects.find_by_email(incoming.origin_address)
         
         if incoming.mailing_list.moderator_controlled:
            if incoming.owner in incoming.mailing_list.moderators.all():
               incoming.create_outgoing()
            else:
               incoming.state = 'reject'
               incoming.save()
            continue
         
         if incoming.owner == None or not incoming.owner in incoming.mailing_list.subscribers.all():
            subject = 'Moderation Request: %s: %s' % (incoming.mailing_list.name, incoming.subject)
            body = render_to_string('interlink/email/moderation_required.txt', { 'incoming_mail': incoming })
            OutgoingMail.objects.create(mailing_list=incoming.mailing_list, moderators_only=True, original_mail=incoming, subject=subject, body=body)
            incoming.state = 'moderate'
            incoming.save()
            continue
         else:
            incoming.create_outgoing()

class IncomingMail(models.Model):
   """An email as popped for a mailing list"""
   mailing_list = models.ForeignKey(MailingList, related_name='incoming_mails')
   origin_address = models.EmailField()
   sent_time = models.DateTimeField()
   subject = models.TextField(blank=True)
   body = models.TextField(blank=True, null=True)
   html_body = models.TextField(blank=True, null=True)

   owner = models.ForeignKey(User, blank=True, null=True, default=None)

   STATES = (('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject'))
   state = models.CharField(max_length=10, choices=STATES, default='raw')

   created = models.DateTimeField(auto_now_add=True)

   objects = IncomingMailManager()

   def reject(self):
      self.state = 'reject'
      self.save()

   def create_outgoing(self):
      if self.mailing_list.subject_prefix:
         subject = '%s %s' % (self.mailing_list.subject_prefix, self.subject)
      else:
         subject = self.subject
      outgoing = OutgoingMail.objects.create(mailing_list=self.mailing_list, original_mail=self, subject=subject, body=self.body, html_body=self.html_body)
      self.state = 'send'
      self.save()
      return outgoing

   @property
   def approve_url(self): return 'http://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_approve', kwargs={'id':self.id}, current_app='interlink'))

   @property
   def reject_url(self): return 'http://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_reject', kwargs={'id':self.id}))

   @property
   def inspect_url(self): return 'http://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_inspect', kwargs={'id':self.id}))

   def __unicode__(self): return '%s: %s' % (self.origin_address, self.subject)

class OutgoingMailManager(models.Manager):
   def send_outgoing(self):
      for mail in self.filter(sent=None):
         if mail.last_attempt and mail.last_attempt > datetime.now() - timedelta(minutes=10): continue
         mail.send()

class OutgoingMail(models.Model):
   """Emails which are consumed by the interlink.tasks.EmailTask"""
   mailing_list = models.ForeignKey(MailingList, related_name='outgoing_mails')
   moderators_only = models.BooleanField(default=False)
   original_mail = models.ForeignKey(IncomingMail, blank=True, null=True, default=None, help_text='The incoming mail which caused this mail to be sent')
   subject = models.TextField(blank=True)
   body = models.TextField(blank=True, null=True)
   html_body = models.TextField(blank=True, null=True)

   attempts = models.IntegerField(blank=False, null=False, default=0)
   last_attempt = models.DateTimeField(blank=True, null=True)
   sent = models.DateTimeField(blank=True, null=True)

   created = models.DateTimeField(auto_now_add=True)

   objects = OutgoingMailManager()

   def send(self):
      if self.sent: return False
      self.last_attempt = datetime.now()
      self.attempts = self.attempts + 1
      self.save()
      try:
         msg = MIMEMultipart('alternative')
         if self.body: msg.attach(MIMEText(self.body, 'plain'))
         if self.html_body: msg.attach(MIMEText(self.html_body, 'html'))
            
         msg['To'] = self.mailing_list.email_address
         if self.original_mail and self.original_mail.owner:
            msg['From'] = '"%s" <%s>' % (self.original_mail.owner.get_full_name(), self.mailing_list.email_address)
         else:
            msg['From'] = self.mailing_list.email_address
         msg['Subject'] = self.subject
         msg['Date'] = email.utils.formatdate()
         if self.original_mail:
            msg['Reply-To'] = self.original_mail.origin_address
         else:
            msg['Reply-To'] = self.mailing_list.email_address
         msg['List-ID'] = self.mailing_list.list_id
         msg['X-CAN-SPAM-1'] = 'This message may be a solicitation or advertisement within the specific meaning of the CAN-SPAM Act of 2003.'
         
         if self.moderators_only:
            recipient_addresses = self.mailing_list.moderator_addresses
         else:
            recipient_addresses = self.mailing_list.subscriber_addresses

         if not settings.IS_TEST and not msg['To'] == '':
            try:
               smtp_server = smtplib.SMTP(self.mailing_list.smtp_host, self.mailing_list.smtp_port)
               smtp_server.login(self.mailing_list.username, self.mailing_list.password)
               smtp_server.sendmail(msg['From'], recipient_addresses + (self.mailing_list.email_address,), msg.as_string())
               smtp_server.quit()
            except:
               traceback.print_exc()
               return False

         if self.original_mail and self.original_mail.state != 'moderate':
            self.original_mail.state = 'sent'
            self.original_mail.save()

         self.sent = datetime.now()
         self.save()
         return True
      except:
         traceback.print_exc()
         return False

   class Meta:
      ordering = ['-created']
      verbose_name_plural = 'outgoing mails'

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
