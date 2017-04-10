import os

from django.template import Library
from django import template
from django.conf import settings
from django.utils.html import format_html
from django.urls import reverse


from nadine.models.profile import EmailAddress

register = template.Library()

@register.simple_tag
def email_verified(email):
    if not email:
        return None
    if not isinstance(email, EmailAddress):
        # Got a string so we should pull the object from the database
        email = EmailAddress.objects.get(email=email)
    if email.is_verified():
        return ""

    html = '<span style="color:red;">( <a target="_top" style="color:red;" href="{}">{}</a> )</span>'
    link = email.get_send_verif_link()
    label = "Not Verified"
    return format_html(html, link, label)
