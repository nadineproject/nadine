from django import template
from django.conf import settings
from django.utils.html import mark_safe, format_html

register = template.Library()

# settings value
@register.simple_tag
def arp_tracker(user):
    url = getattr(settings, 'ARP_TRACKING_URL', "")
    if user and url:
        if not url.endswith('/'):
            url += '/'
        url += user.username
        return format_html("<img src='{}'>",
            mark_safe(url),
        )
    return ""
