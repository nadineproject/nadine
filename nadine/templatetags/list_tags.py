import os
import re
import traceback
from PIL import Image
from django.template import Library
from django import template
from django.utils.html import linebreaks
from django.conf import settings

register = template.Library()


class LoopCommaNode(template.Node):

    def __init__(self):
        self.for_first = template.Variable('forloop.first')
        self.for_last = template.Variable('forloop.last')

    def render(self, context):
        try:
            last = self.for_last.resolve(context)
            if last:
                return ''
            first = self.for_first.resolve(context)
            if last and first:
                return ''
            return ', '
        except template.VariableDoesNotExist:
            print('does not exist')
            return ''


@register.tag(name="loop_comma")
def loop_comma(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires no arguments" % token.contents.split()[0])
    return LoopCommaNode()
