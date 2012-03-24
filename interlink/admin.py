from django.contrib import admin

from models import MailingList, IncomingMail, OutgoingMail

class MailingListAdmin(admin.ModelAdmin):
   raw_id_fields = ['subscribers']
admin.site.register(MailingList, MailingListAdmin)

class IncomingMailAdmin(admin.ModelAdmin):
   list_display = ('sent_time', 'origin_address', 'subject', 'state')
admin.site.register(IncomingMail, IncomingMailAdmin)

class OutgoingMailAdmin(admin.ModelAdmin):
   list_display = ('id', 'original_mail', 'subject', 'sent')

   actions = ['send_mail']
   def send_mail(self, request, queryset):
      mail_queued = 0
      for u in queryset.iterator():
         u.send()
         mail_queued = mail_queued + 1
         if mail_queued == 1:
            self.message_user(request, "1 mail queued to send")
         else:
            self.message_user(request, "%d mails queued to send" % mail_queued)
   send_mail.short_description = "Send mail"

admin.site.register(OutgoingMail, OutgoingMailAdmin)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
