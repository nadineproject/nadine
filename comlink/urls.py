# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from comlink import views

urlpatterns = [
    url(r'^$', views.home, name="comlink_home"),
    url(r'^inbox/(?P<address>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/$', views.inbox, name='comlink_inbox'),
    url(r'^mail/(?P<id>\d+)/$', views.view_mail, name='comlink_mail'),

    url(r'^incoming/$', views.Incoming.as_view(), name='comlink_incoming'),
]
