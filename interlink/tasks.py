from celery.task import task

from models import MailingList, IncomingMail, OutgoingMail


@task(ignore_result=True)
def email_task():
   logger = email_task.get_logger()
   MailingList.objects.fetch_all_mail(logger)
   IncomingMail.objects.process_incoming()
   OutgoingMail.objects.send_outgoing()


# Copyright 2012 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
