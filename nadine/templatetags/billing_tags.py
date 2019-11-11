import os
from django.template import Library
from django import template
from django.conf import settings

VALID = "green"
INVALID = "red"
HAS_PROFILE = "orange"

register = template.Library()

@register.simple_tag
def user_billing_color(user):
    if user.profile.has_valid_billing():
        return VALID
    elif user.profile.has_billing_profile():
        return HAS_PROFILE
    else:
        return INVALID

@register.simple_tag
def valid_billing_color():
    return VALID

@register.simple_tag
def invalid_billing_color():
    return INVALID

@register.simple_tag
def has_profile_color():
    return HAS_PROFILE
