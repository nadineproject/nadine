from django.conf.urls import patterns, include, url
from django.conf import settings

from arpwatch.models import *

urlpatterns = patterns('',
                       url(r'^$', 'hid.views.index'),
                       
                       # Are you the Keymaster?
                       url(r'^keymaster/$', 'hid.views.keymaster'),
)
