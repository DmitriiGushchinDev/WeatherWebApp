from django.urls import path
from . import views

app_name = 'cities'

urlpatterns = [
    path('weather_of_detected_city/', views.weather_of_city, name='weather_of_detected_city'),
    path('city_detail_for_unauthenticated_user/', views.city_detail_for_unauthenticated_user, name='city_detail_for_unauthenticated_user'),
    path('detail/', views.city_detail, name='city_detail'),
    path('add_city_to_profile/', views.add_city_to_profile, name='add_city_to_profile'),
]