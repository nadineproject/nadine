# -*- coding: utf-8 -*-
from django import forms

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

        kwargs['data'] = {self.field_map.get(k, k): v for k, v in mailgun_post.items()}
        super(EmailForm, self).__init__(*args, **kwargs)
        self.fields['attachment-count'] = forms.IntegerField(required=False)

    