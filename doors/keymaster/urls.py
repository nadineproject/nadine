from django.conf.urls import url

from doors.keymaster import views

app_name = 'doors'
urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^logs/$', views.logs, name='logs'),
    url(r'^keys/(?P<username>[^/]+)/$', views.user_keys, name='keys'),
    url(r'^users/$', views.user_list, name='users'),
    url(r'^add_key/$', views.add_key, name='add_key'),
    url(r'^test_door/$', views.test_door, name='test'),
    url(r'^keymaster/$', views.keymaster, name='keymaster'),
]
