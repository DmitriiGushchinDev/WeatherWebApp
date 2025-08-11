from django.urls import path
from . import views

app_name = 'cities'

urlpatterns = [
    path('geolocation/', views.geolocation, name='geolocation'),
    path('weather_of_detected_city/', views.weather_of_city, name='weather_of_detected_city'),
    path('detail/', views.city_detail, name='city_detail'),
]