import os
from django.template import Library
from django import template
from django.conf import settings

register = template.Library()
@register.simple_tag
def valid_billing_color(member):
    if member.has_valid_billing():
        return "black"
    elif member.has_billing_profile():
        return "orange"
    else:
        return "red"

