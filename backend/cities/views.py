import json
import time
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
import requests
from .models import City
from dotenv import load_dotenv
import os
from django.contrib.auth.decorators import login_required
from .serializers import CitySerializer, ProfileSerializer
from .models import Profile
from .ai_generator import generate_city_description
from rest_framework.decorators import api_view
from django.core.cache import cache
from django.http import HttpResponseBadRequest
import hashlib
from django.conf import settings
from django.shortcuts import get_object_or_404


GEO_TTL    = 60 * 60          # 1h   (reverse geocode rarely changes)
WX_TTL     = 60 * 5           # 5min (weather updates frequently)
DESC_TTL   = 60 * 5           # 5min (derived from weather)
CITIES_TTL = 60 * 10          # 10min (user’s cities list)

# ---- HTTP defaults ----
REQ_TIMEOUT = 8  # seconds

load_dotenv()

API_KEY = settings.OPENWEATHER_API_KEY
GEOLOCATION_API = os.getenv('GEOLOCATION_API')
WEATHER_TTL_SECONDS = 15*60
WEATHER_TTL_SECONDS_FOR_LIST = 3*60
GEO_TTL_SECONDS = 1*60
GEOLOCATION_API_BY_LAT_LON = settings.GEOLOCATION_API_BY_LAT_LON
# Create your views here.
@login_required(login_url='auth:login')
def cities_list(request):
    # If not logged in, just return empty list
    if not request.user.is_authenticated:
        return render(request, 'cities/city_list.html', {'cities': []})

    # Current user cities
    cities_qs = request.user.profile.cities.all()
    cities = list(cities_qs)

    # Build a simple, stable signature of the cities set
    # (order-independent: sort by id)
    sig = [(c.id, float(c.latitude), float(c.longitude)) for c in sorted(cities, key=lambda x: x.id)]

    sess = request.session
    cache_obj = sess.get('weather_list_cache')  # {'data': [...], 'ts': float, 'sig': [...]}

    def fetch_and_store():
        lst = []
        for city in cities:
            url = (
                f"https://api.openweathermap.org/data/3.0/onecall"
                f"?lat={city.latitude}&lon={city.longitude}&appid={API_KEY}"
            )
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            lst.append(r.json())

        payload = {'data': lst, 'ts': time.time(), 'sig': sig}
        sess['weather_list_cache'] = payload
        # Ensure Django marks the session as changed even if mutating nested dicts
        request.session.modified = True
        return lst

    # Decide whether to reuse cache
    use_cache = (
        cache_obj is not None and
        (time.time() - cache_obj.get('ts', 0) < WEATHER_TTL_SECONDS_FOR_LIST) and
        (cache_obj.get('sig') == sig)
    )

    if use_cache:
        weather_data_list = cache_obj.get('data', [])
    else:
        weather_data_list = fetch_and_store()

    username = request.user.username
    profile = Profile.objects.get(user__username=username)
    profile_serializer = ProfileSerializer(profile)
    cities = profile_serializer.data['cities']
    cities_list = []
    for city in cities:
        city_obj = City.objects.get(id=city)
        city_serializer = CitySerializer(city_obj)
        cities_list.append(city_serializer.data)

    for i in range(len(cities_list)):
        weather_data_list[i]['geo'] = cities_list[i] 
        print(weather_data_list[i]['geo'])


    return render(request, 'cities/city_list.html', {'cities': weather_data_list})

def _get_json(url, *, params=None, timeout=8):
    """Small helper for JSON GET with timeout and basic error handling."""
    r = requests.get(url, params=params or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()

def weather_of_city(request):
    sess = request.session

    # 1) Geolocate (cache separately)
    geo_cache = sess.get("geo_cache")
    now = time.time()
    if not geo_cache or now - geo_cache.get("fetched_at", 0) > GEO_TTL_SECONDS:
        try:
            geo = _get_json(
                "https://ipgeolocation.abstractapi.com/v1/",
                params={"api_key": GEOLOCATION_API},
            )
        except Exception as e:
            # Fall back to previous geo if present; otherwise bail gracefully
            if geo_cache:
                geo = geo_cache["data"]
            else:
                return HttpResponseServerError("Could not determine location.")
        else:
            geo_cache = {"data": geo, "fetched_at": now}
            sess["geo_cache"] = geo_cache
    else:
        geo = geo_cache["data"]

    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if lat is None or lon is None:
        return HttpResponseServerError("Location missing coordinates.")

    # 2) Weather cache: cache is valid only if coords match AND TTL ok
    wx_cache = sess.get("wx_cache")
    if (
        wx_cache
        and wx_cache.get("lat") == lat
        and wx_cache.get("lon") == lon
        and now - wx_cache.get("fetched_at", 0) < WEATHER_TTL_SECONDS
    ):
        data = wx_cache["data"]
        return render(request, "cities/weather.html", {"data": data, "geo": geo})

    # 3) Fetch fresh weather
    try:
        data = _get_json(
            "https://api.openweathermap.org/data/3.0/onecall",
            params={
                "lat": lat,
                "lon": lon,
                "appid": API_KEY,
                # "units": "metric",          # uncomment if you want °C
                # "exclude": "minutely",      # trim payload if desired
            },
        )
    except Exception as e:
        # If fetch fails but we have a previous cache, use it as a fallback
        if wx_cache and "data" in wx_cache:
            data = wx_cache["data"]
            return render(request, "cities/city_detail.html", {"data": data, "geo": geo})
        return HttpResponseServerError("Weather service unavailable.")

    # 4) Save cache consistently
    sess["wx_cache"] = {
        "lat": lat,
        "lon": lon,
        "data": data,
        "fetched_at": now,
    }

    return render(request, "cities/weather.html", {"data": data, "geo": geo})

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

@login_required(login_url='auth:login')
def geolocation(request):
    url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={GEOLOCATION_API}'
    response = requests.get(url)
    data = response.json()
    print(data)
    return render(request, 'cities/geolocation.html', {'data': data})

def city_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    try:
        # OpenWeather direct geocoding: https://openweathermap.org/api/geocoding-api
        r = requests.get(
            'https://api.openweathermap.org/geo/1.0/direct',
            params={'q': q, 'limit': 8, 'appid': API_KEY},
            timeout=8
        )
        r.raise_for_status()
        arr = r.json()
        # Normalize fields for the frontend
        out = [{
            'name': it.get('name'),
            'country': it.get('country'),
            'state': it.get('state'),
            'lat': it.get('lat'),
            'lon': it.get('lon'),
            'timezone': None,  # could be filled later using One Call or timezone db
        } for it in arr]
        return JsonResponse(out, safe=False)
    except Exception:
        return JsonResponse([], safe=False, status=200)
    
def _coord_key(lat: str, lon: str) -> str:
    return f"{lat.strip()}_{lon.strip()}"

def _hash_dict(d: dict) -> str:
    return hashlib.md5(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()

def _fetch_json(url: str) -> dict:
    r = requests.get(url, timeout=REQ_TIMEOUT)
    r.raise_for_status()
    return r.json()

def city_detail(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    if not lat or not lon:
        return HttpResponseBadRequest("lat and lon are required")

    # OPTIONAL: normalize to fixed precision so keys remain stable
    try:
        lat = f"{float(lat):.4f}"
        lon = f"{float(lon):.4f}"
    except ValueError:
        return HttpResponseBadRequest("lat/lon must be numbers")

    coord_key = _coord_key(lat, lon)

    # ---------- GEO (reverse geocode) ----------
    geo_cache_key = f"geo:{coord_key}"
    geo = cache.get(geo_cache_key)
    if geo is None:
        geo_url = (
            f"https://api.tomtom.com/search/2/reverseGeocode/"
            f"?key={GEOLOCATION_API_BY_LAT_LON}&position={lat},{lon}"
        )
        try:
            geo = _fetch_json(geo_url)
            cache.set(geo_cache_key, geo, GEO_TTL)
        except requests.RequestException:
            geo = {}

    # ---------- WEATHER (OpenWeather One Call) ----------
    wx_cache_key = f"wx:{coord_key}"
    data = cache.get(wx_cache_key)
    if data is None:
        wx_url = (
            f"https://api.openweathermap.org/data/3.0/onecall"
            f"?lat={lat}&lon={lon}&appid={API_KEY}"
        )
        try:
            data = _fetch_json(wx_url)
            cache.set(wx_cache_key, data, WX_TTL)
        except requests.RequestException:
            data = {}

    # ---------- DESCRIPTION (derived; depends on geo+weather) ----------
    # Tie cache to both inputs so changes invalidate automatically
    desc_sig = f"{_hash_dict(data)}:{_hash_dict(geo)}"
    desc_cache_key = f"desc:{desc_sig}"
    description_data = cache.get(desc_cache_key)
    if description_data is None:
        try:
            description_data = generate_city_description(data, geo)
        except Exception:
            description_data = {}
        cache.set(desc_cache_key, description_data, DESC_TTL)

    # ---------- USER CITIES (single query, cached per user) ----------
    username = request.user.username
    cities_cache_key = f"user_cities:{username}"
    cities_list = cache.get(cities_cache_key)

    if cities_list is None:
        profile = get_object_or_404(Profile, user__username=username)
        # serialize once to get ids, then bulk fetch names
        profile_serializer = ProfileSerializer(profile)
        city_ids = profile_serializer.data.get("cities", [])
        # bulk query to avoid N+1
        qs = City.objects.filter(id__in=city_ids).only("id", "name")
        # keep original order if needed
        name_by_id = {c.id: c.name for c in qs}
        cities_list = [name_by_id.get(cid) for cid in city_ids if cid in name_by_id]
        cache.set(cities_cache_key, cities_list, CITIES_TTL)

    context = {
        "geo": geo,
        "data": data,
        "cities_list": cities_list or [],
        "description_data": description_data or {},
    }
    print (geo)
    print(data)
    print(description_data)
    return render(request, "cities/city_detail.html", context)
@api_view(['POST'])
def add_city_to_profile(request):
    payload = request.data
    city = payload.get('name')
    country = payload.get('country')
    lat = payload.get('lat')
    lon = payload.get('lon')
    city_obj = City.objects.create(name=city, country=country, latitude=lat, longitude=lon)
    username = request.user.username
    profile = Profile.objects.get(user__username=username)
    profile.cities.add(city_obj)
    profile.save()
    return JsonResponse({'message': 'City added to profile'})

