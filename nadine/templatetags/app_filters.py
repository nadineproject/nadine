import os
from django import template
from django.template import Library

register = template.Library()

@register.filter
def resource_filter(value):
    if value == 1 or value == '1':
        return 'Coworking Day'
    elif value == 2 or  value == '2':
        return 'Room Booking'
    elif value == 3 or  value == '3':
        return 'Dedicated Desk'
    elif value == 4 or  value == '4':
        return 'Mail Service'
    elif value == 5 or  value == '5':
        return 'Key'
