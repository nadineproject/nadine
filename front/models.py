from datetime import datetime
import traceback

from django.db import models
from django.conf import settings
from django.core.mail import send_mail


class EmailEntryManager(models.Manager):
   def unsent_entries(self): return self.filter(sent__isnull=True).order_by('created')

class EmailEntry(models.Model):
   """Emails which are consumed by the front.tasks.EmailTask"""
   created = models.DateTimeField(auto_now_add=True)
   recipient = models.EmailField()
   subject = models.CharField(max_length=1024, blank=True, null=True)
   body = models.TextField(blank=True, null=True)
   attempts = models.IntegerField(blank=False, null=False, default=0)
   last_attempt = models.DateTimeField(blank=True, null=True)
   sent = models.DateTimeField(blank=True, null=True)

   objects = EmailEntryManager()

   def attempt_to_send(self):
      if self.sent: return False
      self.last_attempt = datetime.now()
      self.attempts = self.attempts + 1
      self.save()
      try:
         if settings.EMAIL_SUBJECT_PREFIX:
            sub = '%s%s' % (settings.EMAIL_SUBJECT_PREFIX, self.subject)
         else:
            sub = self.subject
         send_mail(sub, self.body, settings.EMAIL_ADDRESS, (self.recipient,))
         self.sent = datetime.now()
         self.save()
         return True
      except:
         traceback.print_exc()
         return False

   def __unicode__(self):
      return 'EmailEntry %s: %s' % (self.created, self.sent)

   class Meta:
      verbose_name_plural = 'email entries'

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
