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
            'stripe': hasattr(settings, 'STRIPE_SECRET_KEY'),
            'usaepay': hasattr(settings, 'USA_EPAY_SOAP_KEY'),
            'xero': hasattr(settings, 'XERO_CONSUMER_KEY'),
            'mailgun': hasattr(settings, 'MAILGUN_API_KEY'),
            'google': hasattr(settings, 'GOOGLE_API_KEY'),
            'slack': hasattr(settings, 'SLACK_API_TOKEN'),
            'mailchimp': hasattr(settings, 'MAILCHIMP_API_KEY'),
            'doors': 'doors.keymaster' in settings.INSTALLED_APPS,
            'arp': 'arpwatch' in settings.INSTALLED_APPS,
            'comlink': 'comlink' in settings.INSTALLED_APPS,
        }
        context[self.var_name] = integrations
        return ''
