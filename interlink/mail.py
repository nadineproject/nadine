import poplib
import email
import logging
from datetime import datetime

from django.conf import settings
from django.utils.html import strip_tags
from interlink.models import IncomingMail
from django.contrib.sites.models import Site


logger = logging.getLogger(__name__)

class MailChecker(object):
   """An abstract class for fetching mail from something like a pop or IMAP server"""
   def __init__(self, mailing_list, _logger=None):
      self.mailing_list = mailing_list
      self.logger = _logger or logger

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

   def __init__(self, mailing_list, logger=None):
      super(TestMailChecker, self).__init__(mailing_list, logger)
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
      self.logger.debug("Checking mail from %s:%d" %
                        (self.mailing_list.pop_host, self.mailing_list.pop_port))
      pop_client = poplib.POP3_SSL(self.mailing_list.pop_host, self.mailing_list.pop_port)
      try :
         response = pop_client.user(self.mailing_list.username)
         if not response.startswith('+OK'): raise Exception('Username not accepted: %s' % response)
         response = pop_client.pass_(self.mailing_list.password)
         if not response.startswith('+OK'): raise Exception('Password not accepted: %s' % response)
         stats = pop_client.stat()
         if stats[0] == 0:
            self.logger.debug("No mail")
            return []

         results = []
         self.logger.debug("Processing %d mails" % stats[0])
         for i in range(stats[0]):
            response, mail, _size = pop_client.retr(i+1)
            parser = email.FeedParser.FeedParser()
            parser.feed('\n'.join(mail))
            message = parser.close()

            # Delete and ignore auto responses
            if message['Auto-Submitted'] and message['Auto-Submitted'] != 'no':
               pop_client.dele(i+1)
               continue

            # Delete and ignore messages sent from any list to avoid loops
            if message['List-ID']:
               pop_client.dele(i+1)
               continue

            #TODO Delete and ignore soft bounces

            _name, origin_address = email.utils.parseaddr(message['From'])
            time_struct = email.utils.parsedate(message['Date'])
            if time_struct:
               sent_time = datetime(*time_struct[:-2])
            else:
               sent_time = datetime.now()

            body, html_body, file_names = self.find_bodies(message)
            for file_name in file_names:
               if body: body = '%s\n\n%s' % (body, '\nAn attachment has been dropped: %s' % strip_tags(file_name))
               if html_body: html_body = '%s<br><br>%s' % (html_body, '<div>An attachment has been dropped: %s</div>' % strip_tags(file_name))

            site = Site.objects.get_current()
            if body: body += '\n\nEmail sent to the %s list at http://%s' % (self.mailing_list.name, site.domain)
            if html_body: html_body += u'<br/><div>Email sent to the %s list at <a href="http://%s">%s</a></div>' % (self.mailing_list.name, site.domain, site.name)

            results.append(IncomingMail.objects.create(mailing_list=self.mailing_list, origin_address=origin_address, subject=message['Subject'], body=body, html_body=html_body, sent_time=sent_time, original_message=message))
            pop_client.dele(i+1)
      finally:
         pop_client.quit()

   def find_bodies(self, message):
      """Returns (body, html_body, file_names[]) for this payload, recursing into multipart/alternative payloads if necessary"""
      #if not message.is_multipart(): return (message.get_payload(decode=True), None, [])
      body = None
      html_body = None
      file_names = []
      for bod in message.walk():
         if bod.get_content_type().startswith('text/plain') and not body:
            body = bod.get_payload(decode=True)
            body = body.decode(bod.get_content_charset())
         elif bod.get_content_type().startswith('text/html') and not html_body:
            html_body = bod.get_payload(decode=True)
            html_body = html_body.decode(bod.get_content_charset())
         elif bod.has_key('Content-Disposition') and bod['Content-Disposition'].startswith('attachment; filename="'):
            file_names.append(bod['Content-Disposition'][len('attachment; filename="'):-1])
      return (body, html_body, file_names)

if settings.IS_TEST:
   DEFAULT_MAIL_CHECKER = TestMailChecker
else:
   DEFAULT_MAIL_CHECKER = PopMailChecker



# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
