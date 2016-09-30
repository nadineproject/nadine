import os
from django.template import Library
from django import template
from django.conf import settings
from django.utils.html import format_html

from nadine.models.core import EmailAddress

register = template.Library()

@register.simple_tag
def email_verified(email):
    if isinstance(email, unicode):
        email = EmailAddress.objects.get(email=email)

    html = '<span style="color:{};">( {} )</span>'
    if email.is_verified():
        color = "green"
        label = "Verified"
    else:
        # TODO - make this a link to verify
        color = "red"
        label = "Not Verified"
    return format_html(html, color, label)
