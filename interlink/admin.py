from django.contrib import admin

from interlink.models import MailingList, IncomingMail, OutgoingMail


class MailBase(admin.ModelAdmin):

    def _action(self, request, queryset, f, singular, plural):
        count = 0
        for u in queryset.iterator():
            f(u)
            count = count + 1
            if count == 1:
                self.message_user(request, singular)
            else:
                self.message_user(request, plural % count)


class MailingListAdmin(MailBase):
    raw_id_fields = ['subscribers']
    actions = ['fetch_mail']

    def fetch_mail(self, request, queryset):
        self._action(request, queryset,
                     lambda u: u.fetch_mail(),
                     "Mail fetched from 1 list",
                     "Mail fetched from %s lists")
    fetch_mail.short_description = "Fetch mail"
admin.site.register(MailingList, MailingListAdmin)


class IncomingMailAdmin(MailBase):
    list_display = ('sent_time', 'origin_address', 'subject', 'state')
    list_filter = ('state', 'mailing_list')
    actions = ['process_mail']

    def process_mail(self, request, queryset):
        self._action(request, queryset,
                     lambda u: u.process(),
                     "1 incoming mail processed",
                     "%s incoming mails processed")
    process_mail.short_description = "Process mail"
admin.site.register(IncomingMail, IncomingMailAdmin)


class OutgoingMailAdmin(MailBase):
    list_display = ('id', 'original_mail', 'subject', 'sent')

    actions = ['send_mail']

    def send_mail(self, request, queryset):
        self._action(request, queryset,
                     lambda u: u.send(),
                     "1 mail sent",
                     "%s mails sent")
    send_mail.short_description = "Send mail"

admin.site.register(OutgoingMail, OutgoingMailAdmin)

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
