import email
import logging
import sys
from datetime import datetime, timedelta
from collections import defaultdict

from django.db import models
from django.db.models import Q, Sum
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.mail import get_connection, EmailMultiAlternatives
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from staff.models import Member, Membership
from interlink.message import MailingListMessage

logger = logging.getLogger(__name__)

def user_by_email(email):
   users = User.objects.filter(email__iexact=email)
   if len(users) > 0: return users[0]
   members = Member.objects.filter(email2__iexact=email)
   if len(members) > 0: return members[0].user
   return None
User.objects.find_by_email = user_by_email

def membership_save_callback(sender, **kwargs):
   """When a membership is created, add the user to any opt-out mailing lists"""
   membership = kwargs['instance']
   created = kwargs['created']
   if not created: return
   # If the member is just switching from one membership to another, don't change subscriptions
   if Membership.objects.filter(member=membership.member, end_date=membership.start_date-timedelta(days=1)).count() != 0: return
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
         if user in ml.subscribers.all():
            ml.subscribers.remove(user)

   def fetch_all_mail(self, logger=None):
      """Fetches mail for all mailing lists and returns an array of mailing_lists which reported failures"""
      for ml in self.all():
         ml.fetch_mail(logger)

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

   throttle_limit = models.IntegerField(default=0, help_text='The number of recipients in 10 minutes this mailing list is limited to. Default is 0, which means no limit.')

   objects = MailingListManager()

   class LimitExceeded(Exception):
      pass

   def fetch_mail(self, logger=None):
      """Fetches incoming mails from the mailing list."""
      # We could bring back the configurability of the mail checker,
      # but right now it doesn't really *test* anything..
      from interlink.mail import PopMailChecker
      checker = PopMailChecker(self, logger)
      return checker.fetch_mail()

   def get_smtp_connection(self):
      fail_silently = getattr(settings, 'INTERLINK_MAILS_FAIL_SILENTLY', False)
      return get_connection(host=self.smtp_host,
                            port=self.smtp_port,
                            username=self.username,
                            password=self.password,
                            fail_silently=fail_silently)

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

   def create_incoming(self, message, commit=True):
      "Parses an email message and creates an IncomingMail from it."
      _name, origin_address = email.utils.parseaddr(message['From'])
      time_struct = email.utils.parsedate(message['Date'])
      if time_struct:
         sent_time = datetime(*time_struct[:-2])
      else:
         sent_time = timezone.localtime(timezone.now())

      body, html_body, file_names = self.find_bodies(message)
      for file_name in file_names:
         if body:
            body = '%s\n\n%s' % (body, '\nAn attachment has been dropped: %s' % strip_tags(file_name))
         if html_body:
            html_body = '%s<br><br>%s' % (html_body, '<div>An attachment has been dropped: %s</div>' % strip_tags(file_name))

      site = Site.objects.get_current()
      if body:
         body += '\n\nEmail sent to the %s list at https://%s' % (self.name, site.domain)
      if html_body:
         html_body += u'<br/><div>Email sent to the %s list at <a href="https://%s">%s</a></div>' % (self.name, site.domain, site.name)

      incoming = IncomingMail(mailing_list=self,
                             origin_address=origin_address,
                             subject=message['Subject'],
                             body=body,
                             html_body=html_body,
                             sent_time=sent_time,
                             original_message=str(message))
      if commit:
         incoming.save()
      return incoming

   def find_bodies(self, message):
      """Returns (body, html_body, file_names[]) for this payload, recursing into multipart/alternative payloads if necessary"""
      #if not message.is_multipart(): return (message.get_payload(decode=True), None, [])
      body = None
      html_body = None
      file_names = []
      for bod in message.walk():
         if bod.get_content_type().startswith('text/plain') and not body:
            body = bod.get_payload(decode=True)
            body = body.decode(bod.get_content_charset('ascii'))
         elif bod.get_content_type().startswith('text/html') and not html_body:
            html_body = bod.get_payload(decode=True)
            html_body = html_body.decode(bod.get_content_charset('ascii'))
         elif bod.has_key('Content-Disposition') and bod['Content-Disposition'].startswith('attachment; filename="'):
            file_names.append(bod['Content-Disposition'][len('attachment; filename="'):-1])
      return (body, html_body, file_names)

   def incoming_mail(self, limit=25, sent_only=True):
      if sent_only:
         return IncomingMail.objects.filter(mailing_list=self, state="sent").order_by("sent_time").reverse()[:limit]
      else:
         return IncomingMail.objects.filter(mailing_list=self).order_by("sent_time").reverse()[:limit]

def user_mailing_list_memberships(user):
   """Returns an array of tuples of <MailingList, is_subscriber> for a User"""
   return [(ml, user in ml.subscribers.all()) for ml in MailingList.objects.all()]
User.mailing_list_memberships = user_mailing_list_memberships


class IncomingMailManager(models.Manager):
   def process_incoming(self):
      for incoming in self.filter(state='raw'):
         incoming.process()

class IncomingMail(models.Model):
   """An email as popped for a mailing list"""
   mailing_list = models.ForeignKey(MailingList, related_name='incoming_mails')
   origin_address = models.EmailField()
   sent_time = models.DateTimeField()
   subject = models.TextField(blank=True)
   body = models.TextField(blank=True, null=True)
   html_body = models.TextField(blank=True, null=True)
   original_message = models.TextField(blank=True)

   owner = models.ForeignKey(User, blank=True, null=True, default=None)

   STATES = (('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject'))
   state = models.CharField(max_length=10, choices=STATES, default='raw')

   created = models.DateTimeField(auto_now_add=True)

   objects = IncomingMailManager()

   def reject(self):
      self.state = 'reject'
      self.save()

   @property
   def _prefix_subject(self):
      subject = self.subject
      subject_prefix = self.mailing_list.subject_prefix

      if not subject_prefix:
         return subject

      # Reply handling: if the prefix is already in the subject, don't prefix
      if subject_prefix in subject:
         return subject

      # Otherwise prefix
      return ' '.join((subject_prefix, subject))

   def sender_subscribed(self):
      return self.owner in self.mailing_list.subscribers.all()

   def clean_subject(self):
      subject = self.subject
      prefix = self.mailing_list.subject_prefix
      if prefix:
         index = subject.find(prefix)
         if index >= 0:
            subject = subject[index + len(prefix):]
      return subject.strip()

   def is_moderated_subject(self):
      s = self.subject.lower()
      if "auto-reply" in s: 
         return True
      if "auto reply" in s: 
         return True
      if "automatic reply" in s: 
         return True
      if "out of office" in s: 
         return True
      return False

   def create_outgoing(self):
      subject = self._prefix_subject
      outgoing = OutgoingMail.objects.create(mailing_list=self.mailing_list, original_mail=self, subject=subject, body=self.body, html_body=self.html_body)
      self.state = 'send'
      self.save()
      return outgoing

   def process(self):
      self.owner = User.objects.find_by_email(self.origin_address)

      if self.mailing_list.moderator_controlled:
         if self.owner in self.mailing_list.moderators.all():
            self.create_outgoing()
         else:
            self.state = 'reject'
            self.save()

      elif self.owner == None or not self.sender_subscribed() or self.is_moderated_subject():
         subject = 'Moderation Request: %s: %s' % (self.mailing_list.name, self.subject)
         body = render_to_string('interlink/email/moderation_required.txt', { 'incoming_mail': self })
         OutgoingMail.objects.create(mailing_list=self.mailing_list, moderators_only=True, original_mail=self, subject=subject, body=body)
         self.state = 'moderate'
         self.save()

      else:
         self.create_outgoing()

   def get_user(self):
      return user_by_email(self.origin_address)

   @property
   def approve_url(self): return 'https://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_approve', kwargs={'id':self.id}, current_app='interlink'))

   @property
   def reject_url(self): return 'https://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_reject', kwargs={'id':self.id}))

   @property
   def inspect_url(self): return 'https://%s%s' % (Site.objects.get_current().domain, reverse('interlink.views.moderator_inspect', kwargs={'id':self.id}))

   def __unicode__(self): return '%s: %s' % (self.origin_address, self.subject)

class OutgoingMailManager(models.Manager):
   def send_outgoing(self):
      # First, get all the mails we want to send
      to_send = (self.select_related('mailing_list')
                     .filter(sent__isnull=True)
                     .filter(Q(last_attempt__isnull=True) |
                             Q(last_attempt__lt=timezone.localtime(timezone.now()) - timedelta(minutes=10))))
      # This dict is indexed by the mailing list
      # and contains a list of each mail that should be sent using that smtp info
      d = defaultdict(list)
      for m in to_send:
         d[m.mailing_list].append(m)

      # Once we have this, we can go through each key value pair,
      # make a connection to the server, and send them all.
      for ml, mails in d.iteritems():
         try:
            conn = ml.get_smtp_connection()
            conn.open()
            for m in mails:
               try:
                  m.send(conn)
               except MailingList.LimitExceeded, e:
                  logger.warning("Limit exceeded: " + str(e),
                                 exc_info=sys.exc_info(),
                                 extra={'exception': e})
                  break

         finally:
            conn.close()

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
   sent_recipients = models.IntegerField(default=0)

   created = models.DateTimeField(auto_now_add=True)

   objects = OutgoingMailManager()

   def _check_throttle(self, msg):
      num_recipients = len(msg.recipients())
      limit = self.mailing_list.throttle_limit
      if not limit:
         return len(msg.recipients())

      r = (OutgoingMail.objects.filter(mailing_list=self.mailing_list,
                                       sent__gt=timezone.localtime(timezone.now()) - timedelta(minutes=10))
                               .aggregate(Sum('sent_recipients')))
      num_sent_recipients = r['sent_recipients__sum'] or 0

      if num_sent_recipients + num_recipients > limit:
         num = num_sent_recipients + num_recipients
         raise MailingList.LimitExceeded("%d exceeds limit of %d recipients for this list" %
                                         (num, limit))
      return num_recipients

   def send(self, connection=None):
      if self.sent:
         return

      args = {
         'subject': self.subject,
         'body': self.body
      }

      if self.moderators_only:
         email_cls = EmailMultiAlternatives
         args['to'] = self.mailing_list.moderator_addresses
      else:
         email_cls = MailingListMessage
         args['to'] = [self.mailing_list.email_address]
         args['bcc'] = self.mailing_list.subscriber_addresses

      headers = {
         #'Date': email.utils.formatdate(),  # Done by default in Django
         'Sender': self.mailing_list.email_address,
         #'Reply-To': self.mailing_list.email_address,
         'List-ID': self.mailing_list.list_id,
         'X-CAN-SPAM-1': 'This message may be a solicitation or advertisement within the specific meaning of the CAN-SPAM Act of 2003.'
      }

      # Determine the from address
      if self.original_mail:
         org = self.original_mail
         if org.owner:
            # Sender is a known user
            args['from_email'] = email.utils.formataddr((org.owner.get_full_name(), org.owner.email))
         elif org.origin_address and not self.moderators_only:
            args['from_email'] = self.original_mail.origin_address

      # If it wasn't set, we have nothing better than just to send it from the mailing list
      args.setdefault('from_email', self.mailing_list.email_address)
      # Replies go to the originating user, not the list
      headers['Reply-To'] = args['from_email']

      if self.original_mail and not self.moderators_only:
         # Attempt to propagate certain headers
         msg = email.message_from_string(str(self.original_mail.original_message))
         for hdr in ('Message-ID', 'References', 'In-Reply-To'):
            if hdr in msg:
               headers[hdr] = msg[hdr].replace("\r", "").replace("\n", " ")

      args['headers'] = headers

      msg = email_cls(**args)
      # Is this really the case? Right now it is, until we don't use the
      # body or html_body and instead edit the MIME version itself.
      msg.encoding = 'utf-8'
      if self.html_body:
         msg.attach_alternative(self.html_body, 'text/html')

      num_recipients = self._check_throttle(msg)

      # Update this after we pass the throttle but before we actually try to send.
      self.last_attempt = timezone.localtime(timezone.now())
      self.attempts = self.attempts + 1
      self.save()

      conn = connection or self.mailing_list.get_smtp_connection()
      conn.send_messages([msg])

      if self.original_mail and self.original_mail.state != 'moderate':
         self.original_mail.state = 'sent'
         self.original_mail.save()

      self.sent_recipients = num_recipients
      self.sent = timezone.localtime(timezone.now())
      self.save()

   class Meta:
      ordering = ['-created']
      verbose_name_plural = 'outgoing mails'

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
