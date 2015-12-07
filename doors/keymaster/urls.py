from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('doors.keymaster.views',
                       url(r'^$', 'index'),
                       url(r'^test_door/$', 'test_door'),
                       
                       # Are you the Keymaster?
                       url(r'^keymaster/$', 'keymaster'),
)
