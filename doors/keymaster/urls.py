from django.conf.urls import url

from doors.keymaster import views

urlpatterns = [
    url(r'^$', views.index, name='doors_index'),
    url(r'^logs/$', views.logs, name='doors_logs'),
    url(r'^keys/(?P<username>[^/]+)/$', views.user_keys, name='doors_keys'),
    url(r'^users/$', views.user_list, name='doors_users'),
    url(r'^add_key/$', views.add_key, name='doors_add_key'),
    url(r'^test_door/$', views.test_door, name='doors_test'),
    url(r'^keymaster/$', views.keymaster, name='doors_keymaster'),
]
