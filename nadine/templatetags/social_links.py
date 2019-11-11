import re
from django import template
from django.conf import settings

register = template.Library()

@register.tag(name="load_social_urls")
def social_urls(parser, token):
    token_contents = token.split_contents()
    var_name = 'social_urls'
    if len(token_contents) >= 3 and token_contents[1] == 'as':
        var_name = token_contents[2]
    return SocialNode(var_name)

class SocialNode(template.Node):
    def __init__(self, var_name):
        self.var_name = var_name

    def render(self, context):
        social_urls = {}
        if hasattr(settings, 'FACEBOOK_URL'):
            social_urls['facebook'] = settings.FACEBOOK_URL
        if hasattr(settings, 'TWITTER_URL'):
            social_urls['twitter'] = settings.TWITTER_URL
        if hasattr(settings, 'YELP_URL'):
            social_urls['yelp'] = settings.YELP_URL
        if hasattr(settings, 'INSTAGRAM_URL'):
            social_urls['instagram'] = settings.INSTAGRAM_URL
        context[self.var_name] = social_urls
        return ''
