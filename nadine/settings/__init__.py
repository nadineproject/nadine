# This is a convenience to load a local_settings.py module by default.
#
# You can tell Django to load environment-specific settings modules with the
# DJANGO_SETTINGS_MODULE environment variable.
#
# https://docs.djangoproject.com/en/1.11/topics/settings/#designating-the-settings
# https://speakerdeck.com/jacobian/the-best-and-worst-of-django?slide=81

from .local_settings import *
