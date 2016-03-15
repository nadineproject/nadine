from django.conf.urls import url

from doors.keymaster import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^keys/(?P<username>[^/]+)/$', views.user_keys),
    url(r'^users/$', views.user_list),
    url(r'^add_key/$', views.add_key),
    url(r'^test_door/$', views.test_door),
    url(r'^keymaster/$', views.keymaster),
]
