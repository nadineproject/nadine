# -*- coding: utf-8 -*-
from django import forms

from comlink.exceptions import DroppedMailException

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

        mailgun_data = {self.field_map.get(k, k): v for k, v in mailgun_post.items()}
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
