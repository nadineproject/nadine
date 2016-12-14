import os
from django import template
from django.template import Library

register = template.Library()

@register.filter
def gender_filter(value):
    if value == 'F':
        return 'Female'
    elif value == 'M':
        return 'Male'
    elif value == 'O':
        return 'Other'
    else:
        return 'Not shared'
