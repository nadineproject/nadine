# -*- coding: utf-8 -*-
from django.urls import path,re_path


from comlink import views

app_name = 'comlink'
urlpatterns = [
    path('', views.home, name="home"),
    path('incoming/', views.Incoming.as_view(), name='incoming'),
    path('mail/<int:id>/', views.view_mail, name='mail'),
    re_path(r'inbox/(?P<address>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/$', views.inbox, name='inbox'),
]
