from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('doors.keymaster.views',
                       url(r'^$', 'index'),
                       url(r'^add_key/$', 'add_key'),
                       url(r'^test_door/$', 'test_door'),
                       
                       # Are you the Keymaster?
                       url(r'^keymaster/$', 'keymaster'),
)
