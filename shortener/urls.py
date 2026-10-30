from django.urls import path

from . import views

app_name = 'shortener'

urlpatterns = [
    path('api/urls/', views.shorten_url, name='shorten'),
    path('api/urls/<str:code>/', views.resolve_url, name='resolve'),
]
