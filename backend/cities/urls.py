from django.urls import path
from . import views

app_name = 'cities'

urlpatterns = [
    path('', views.city_detail, name='weather_of_detected_city'),
    path('city_detail_for_unauthenticated_user/', views.city_detail_for_unauthenticated_user, name='city_detail_for_unauthenticated_user'),
    path('city-detail/', views.city_detail, name='city_detail'),
    path('add_city_to_profile/', views.add_city_to_profile, name='add_city_to_profile'),
    path('delete_city/<str:city_name>/', views.delete_city, name='delete_city'),

]