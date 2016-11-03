# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include
from comlink.views import Incoming

urlpatterns = patterns('',
    url('^incoming/$', Incoming.as_view(), {}, 'mg-incoming'),
)
