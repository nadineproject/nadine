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
        self.month_history_var = template.Variable('month')
        self.type_var = template.Variable('type')

    def render(self, context):
        try:
            month_history = self.month_history_var.resolve(context)
            datum_type = self.type_var.resolve(context)
            return month_history.data[datum_type]
        except template.VariableDoesNotExist:
            print('does not exist')
            return ''


@register.tag(name="month_history_datum")
def month_history_datum(parser, token):
    try:
        tag_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires no arguments" % token.contents.split()[0])
    return LoopCommaNode()
