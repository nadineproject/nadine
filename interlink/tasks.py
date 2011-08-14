from datetime import datetime, timedelta
import traceback

from interlink.scheduler import Task

class EmailTask(Task):
   """A recurring task which checks the pending email records and either relays or moderates them."""
   def __init__(self, loopdelay=120, initdelay=5):
      Task.__init__(self, self.perform_task, loopdelay, initdelay)
      self.name = "EmailTask"

   def perform_task(self):
      from interlink import DEFAULT_MAIL_CHECKER
      from models import MailingList
      try:
         for mailing_list in MailingList.objects.all():
            DEFAULT_MAIL_CHECKER(mailing_list).fetch_mail()
      except:
         traceback.print_exc()
      MailingList.objects.process_incoming()
      MailingList.objects.send_outgoing()

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
