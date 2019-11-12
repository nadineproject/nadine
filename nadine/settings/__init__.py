# This is a convenience to load a local_settings.py module by default.
#
# You can tell Django to load environment-specific settings modules with the
# DJANGO_SETTINGS_MODULE environment variable.
#
# https://docs.djangoproject.com/en/1.11/topics/settings/#designating-the-settings
# https://speakerdeck.com/jacobian/the-best-and-worst-of-django?slide=81

import os
import imp


# First check to see if there is an existing local settings file
if os.path.isfile('nadine/settings/local_settings.py'):
    # print("Loading local settings file...")
    from .local_settings import *
else:
    from .base import *

# Look for a theme settings file and load that too if we have it
if os.path.isfile('themes/active/theme_settings.py'):
    # print("Loading theme settings file...")
    sys.path.append('themes/active')
    theme_settings = imp.load_source('themes.active.theme_settings', 'themes/active/theme_settings.py')
    from theme_settings import *
