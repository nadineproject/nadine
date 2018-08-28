from django.urls import path

from doors.keymaster import views


app_name = 'doors'
urlpatterns = [
    path('', views.home, name='home'),
    path('logs/', views.logs, name='logs'),
    path('keys/<username>/', views.user_keys, name='keys'),
    path('users/', views.user_list, name='users'),
    path('add_key/', views.add_key, name='add_key'),
    path('test_door/', views.test_door, name='test'),
    path('keymaster/', views.keymaster, name='keymaster'),
]
