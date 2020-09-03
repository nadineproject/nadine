from django.urls import path

from . import views

app_name = 'elocky'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/delete_recu/<int:access_id>', views.delete_recu, name='delete'),
    path('<int:pk>/delete_exep/<int:access_id>', views.delete_exep, name='delete'),
    path('<int:pk>/create_recu', views.create_recu, name='create'),
    path('<int:pk>/create_exep', views.create_exep, name='create')
]
