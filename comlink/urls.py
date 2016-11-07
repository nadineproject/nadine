# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from comlink import views

urlpatterns = [
    url(r'^$', views.home, name="comlink_home"),
    url(r'^mail/(?P<id>\d+)/$', views.view_mail, name='comlink_mail'),

    url(r'^incoming/$', views.Incoming.as_view(), name='comlink_incoming'),
]
