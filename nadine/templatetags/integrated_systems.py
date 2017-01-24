import re
from django import template
from django.conf import settings

register = template.Library()

@register.tag(name="load_integrations")
def integrations(parser, token):
    token_contents = token.split_contents()
    var_name = 'integrations'
    if len(token_contents) >= 3 and token_contents[1] == 'as':
        var_name = token_contents[2]
    return IntegrationsNode(var_name)

class IntegrationsNode(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        integrations = {
            'usaepay': hasattr(settings, 'USA_EPAY_KEY'),
            'xero': hasattr(settings, 'XERO_CONSUMER_KEY'),
            'mailgun': hasattr(settings, 'MAILGUN_API_KEY'),
            'google': hasattr(settings, 'GOOGLE_API_KEY'),
            'slack': hasattr(settings, 'SLACK_API_TOKEN'),
            'hid': hasattr(settings, 'HID_ENCRYPTION_KEY'),
            'mailchimp': hasattr(settings, 'MAILCHIMP_API_KEY'),
        }
        context[self.var_name] = integrations
        return ''
