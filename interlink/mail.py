import time
import poplib, email
from datetime import datetime, date, timedelta

from django.conf import settings
from interlink.models import IncomingMail

class MailChecker(object):
   """An abstract class for fetching mail from something like a pop or IMAP server"""
   def __init__(self, mailing_list):
      self.mailing_list = mailing_list
      
   def fetch_mail(self):
      """
      Talk to the remote service, fetch the mail, create IncomingMail records
      Returns an array of new IncomingMail objects
      """
      raise NotImplementedError


TEST_INCOMING_MAIL = {} # a map of MailingLists to arrays of maps like so: {'origin_address':origin_address, 'subject':subject, 'sent_time':sent_time, 'body':body }

def add_test_incoming(mailing_list, origin_address, subject, body, sent_time=None):
   # Queue up an incoming mail for the TestMailChecker
   sent_time = sent_time or datetime.now()
   TEST_INCOMING_MAIL[mailing_list].append({'origin_address':origin_address, 'subject':subject, 'sent_time':sent_time, 'body':body })


class TestMailChecker(MailChecker):
   """A queue based mock object used in test suites."""
   
   def __init__(self, mailing_list):
      super(TestMailChecker, self).__init__(mailing_list)
      if not TEST_INCOMING_MAIL.has_key(mailing_list): TEST_INCOMING_MAIL[mailing_list] = []
		
   def fetch_mail(self):
      """
      Pops mail from the TEST_INCOMING_MAIL queue and creates IncomingMail records for them
      Returns an array of IncomingMail that were created
      """
      results = []
      while len(TEST_INCOMING_MAIL[self.mailing_list]) > 0:
         mail = TEST_INCOMING_MAIL[self.mailing_list].pop(0)
         results.append(IncomingMail.objects.create(mailing_list=self.mailing_list, origin_address=mail['origin_address'], subject=mail['subject'], body=mail['body'], sent_time=mail['sent_time']))
      return results

class PopMailChecker(MailChecker):
   
   def fetch_mail(self):
      """Pops mail from the pop server and writes them as IncomingMail"""
      pop_client = poplib.POP3_SSL(self.mailing_list.pop_host, self.mailing_list.pop_port)
      response = pop_client.user(self.mailing_list.username)
      if not response.startswith('+OK'): raise Exception('Username not accepted: %s' % response)
      response = pop_client.pass_(self.mailing_list.password)
      if not response.startswith('+OK Logged in'): raise Exception('Password not accepted: %s' % response)
      stats = pop_client.stat()
      if stats[0] == 0: return []

      results = []
      for i in range(stats[0]):
         response, mail, size = pop_client.retr(i+1)
         parser = email.FeedParser.FeedParser()
         parser.feed('\n'.join(mail))
         message = parser.close()

         # Delete and ignore auto responses
         if message['Auto-Submitted'] and message['Auto-Submitted'] != 'no':
            pop_client.dele(i+1)
            continue
            
         # Delete and ignore messages sent from any list
         if message['List-ID']:
            pop_client.dele(i+1)
            continue

         #TODO Delete and ignore soft bounces

         name, origin_address = email.utils.parseaddr(message['From'])
         time_struct = email.utils.parsedate(message['Date'])
         if time_struct:
            sent_time = datetime(*time_struct[:-2])
         else:
            sent_time = datetime.now()
         if message.is_multipart():
            for bod in  message.get_payload():
               body = bod.get_payload()
               if body: break
         else:
            body = message.get_payload()
         results.append(IncomingMail.objects.create(mailing_list=self.mailing_list, origin_address=origin_address, subject=message['Subject'], body=body, sent_time=sent_time))
         pop_client.dele(i+1)
        
      pop_client.quit()

if settings.IS_TEST:
   DEFAULT_MAIL_CHECKER = TestMailChecker
else:
   DEFAULT_MAIL_CHECKER = PopMailChecker


   
# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
