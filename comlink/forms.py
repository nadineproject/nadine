# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings

from comlink import mailgun
from comlink.exceptions import DroppedMailException
from comlink.models import MailingList


class MailingListSubscriptionForm(forms.Form):
    subscribe = forms.CharField(required=False, widget=forms.HiddenInput)
    mailing_list_id = forms.IntegerField(required=True, widget=forms.HiddenInput)

    def save(self, user):
        mailing_list = MailingList.objects.get(pk=self.cleaned_data['mailing_list_id'])
        #body = 'So says https://%s ' % Site.objects.get_current().domain
        subject = "Nadine Subscribe/Unsubscribe Form"
        if self.cleaned_data['subscribe'] == 'true' and (user.profile.is_active() or user.is_staff):
            mailing_list.subscribe(user)
            subject = '%s subscribed to %s' % (user.get_full_name(), mailing_list.name)
        elif self.cleaned_data['subscribe'] == 'false' and user in mailing_list.subscribers.all():
            mailing_list.unsubscribe(user)
            subject = '%s unsubscribed from %s' % (user.get_full_name(), mailing_list.name)

        # Send a notification to the team
        mailgun_data = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [settings.TEAM_EMAIL_ADDRESS, ],
            "subject": subject,
            "text": "So says Nadine!",
        }
        mailgun.mailgun_send(mailgun_data, inject_list_id=False)

        return True


class EmailForm(forms.ModelForm):

    field_map = {
        'body-html': 'body_html',
        'body-plain': 'body_plain',
        'content-id-map': 'content_id_map',
        'from': 'from_str',
        'message-headers': 'message_headers',
        'recipient': 'recipient',
        'sender': 'sender',
        'stripped-html': 'stripped_html',
        'stripped-signature': 'stripped_signature',
        'stripped-text': 'stripped_text',
        'subject': 'subject'
    }

    def __init__(self, mailgun_post=None, *args, **kwargs):
        if not mailgun_post:
            raise Exception("No mailgun post passed. Unbound form not supported.")

        mailgun_data = {self.field_map.get(k, k): v for k, v in list(mailgun_post.items())}
        message_headers = mailgun_data['message_headers']
        message_header_keys = [item[0] for item in message_headers]

        # A List-Id header will only be present if it has been added manually in
        # this function, ie, if we have already processed this message.
        if mailgun_post.get('List-Id') or 'List-Id' in message_header_keys:
            raise DroppedMailException("List-Id header was found!")

        # If 'Auto-Submitted' in message_headers or message_headers['Auto-Submitted'] != 'no':
        if 'Auto-Submitted' in message_header_keys:
            raise DroppedMailException("Message appears to be auto-submitted")

        kwargs['data'] = mailgun_data
        super(EmailForm, self).__init__(*args, **kwargs)
        self.fields['attachment-count'] = forms.IntegerField(required=False)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
