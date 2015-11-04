from django.conf.urls import patterns, include, url
from django.conf import settings

from hid.models import *

urlpatterns = patterns('hid.views',
                       url(r'^$', 'index'),
                       url(r'^test_door/$', 'test_door'),
                       
                       # Are you the Keymaster?
                       url(r'^keymaster/$', 'keymaster'),
)
