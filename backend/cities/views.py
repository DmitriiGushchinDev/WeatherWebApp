import time
from django.shortcuts import render
import requests
from .models import City
from dotenv import load_dotenv
import os
from django.contrib.auth.decorators import login_required
load_dotenv()

API_KEY = os.getenv('OPENWEATHER_API_KEY')
GEOLOCATION_API = os.getenv('GEOLOCATION_API')
WEATHER_TTL_SECONDS = 15*60
# Create your views here.
@login_required
def cities_list(request):
    cities = City.objects.all()
    return render(request, 'cities/city_list.html', {'cities': cities})

def weather_of_city(request):
    sess = request.session
    if 'weather_data' in sess:
        weather_data = sess['weather_data']
        if time.time() - weather_data['timestamp'] < WEATHER_TTL_SECONDS:
            print('IT WORKs')
            return render(request, 'cities/weather_of_city.html', {'weather_data': weather_data})
    if 'geolocation_data' in sess:
        geolocation_data = sess['geolocation_data']
        latitude = geolocation_data['latitude']
        longitude = geolocation_data['longitude']
        url = f'https://api.openweathermap.org/data/3.0/onecall?lat={latitude}&lon={longitude}&appid={API_KEY}'
        response = requests.get(url)
        data = response.json()
        print(data)
        print(data['current']['temp'])
        print('IT STILL WORKS')
        return render(request, 'cities/weather_of_detected.html', {'data': data})
    url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={GEOLOCATION_API}'
    response = requests.get(url)
    data = response.json()
    url = f'https://api.openweathermap.org/data/3.0/onecall?lat={data['latitude']}&lon={data['longitude']}&appid={API_KEY}'
    response = requests.get(url)
    data = response.json()
    print(data)
    print(data['current']['temp'])
    print('IT DOESNT WORK')
    sess['weather_data'] = data
    sess['weather_data']['timestamp'] = time.time()
    sess['geolocation_data'] = data
    return render(request, 'cities/weather_of_detected.html', {'data': data})


def weather_of_detected_city(request):
    url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={GEOLOCATION_API}'
    response = requests.get(url)
    data = response.json()
    url = f'https://api.openweathermap.org/data/3.0/onecall?lat={data['latitude']}&lon={data['longitude']}&appid={API_KEY}'
    response = requests.get(url)
    data = response.json()
    print(data)
    print(data['current']['temp'])
    return render(request, 'cities/weather_of_detected.html', {'data': data})


def geolocation(request):
    url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={GEOLOCATION_API}'
    response = requests.get(url)
    data = response.json()
    print(data)
    return render(request, 'cities/geolocation.html', {'data': data})

