from django.urls import path
from . import views

app_name = 'cities'

urlpatterns = [
    path('geolocation/', views.geolocation, name='geolocation'),
]