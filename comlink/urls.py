# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from comlink.views import Incoming

urlpatterns = [
    url('^incoming/$', Incoming.as_view(), {}, 'mg-incoming'),
]
