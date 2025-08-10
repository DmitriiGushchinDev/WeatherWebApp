import os,requests, datetime as dt
from django.conf import settings
from django.core.cache import cache
from dateutil import tz


OWM_GEO = "https://api.openweathermap.org/geo/1.0/direct"
OWM_ONECALL = "https://api.openweathermap.org/data/3.0/onecall"

API_KEY = settings.OPENWEATHER_API_KEY
UNITS = settings.OPENWEATHER_UNITS
LANG  = settings.OPENWEATHER_LANG
TIMEOUT = settings.REQUESTS_TIMEOUT

class OpenWeatherError(Exception):
    pass

def geocode_city(q:str,limit: int = 1):
    if not API_KEY:
        raise OpenWeatherError("OpenWeather API key is not set")
    
    key = f"owm:geo:{q}:{limit}"
    if (cached := cache.get(key)) is not None:
        return cached
    r = requests.get(OWM_GEO, params={"q": q, "limit": limit, "appid": API_KEY}, timeout=TIMEOUT)
    if r.status_code != 200:
        raise OpenWeatherError(f"Geocode failed: {r.status_code} {r.text[:200]}")
    data = r.json() or []
    cache.set(key, data, 60 * 60 * 24)  # 24h
    return data

def one_call(lat: float, lon: float, exclude=("minutely",)):
    """One Call 3.0 for current/hourly/daily + alerts."""
    if not API_KEY:
        raise OpenWeatherError("Missing OPENWEATHER_API_KEY.")
    key = f"owm:one:{round(lat,3)}:{round(lon,3)}:{UNITS}:{LANG}"
    if (cached := cache.get(key)) is not None:
        return cached

    params = {
        "lat": lat, "lon": lon, "appid": API_KEY,
        "units": UNITS, "lang": LANG, "exclude": ",".join(exclude)
    }
    r = requests.get(OWM_ONECALL, params=params, timeout=TIMEOUT)
    if r.status_code != 200:
        raise OpenWeatherError(f"OneCall failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    cache.set(key, data, 60 * 15)  # 15 minutes
    return data

def with_local_times(payload: dict, tz_name: str | None = None):
    """Add *_local fields derived from UNIX timestamps."""
    if not payload: return payload
    zone = tz.gettz(tz_name) if tz_name else None
    def conv(ts): 
        d = dt.datetime.utcfromtimestamp(ts).replace(tzinfo=dt.timezone.utc)
        return d.astimezone(zone) if zone else d
    cur = payload.get("current") or {}
    for k in ("sunrise","sunset","dt"):
        if k in cur: cur[f"{k}_local"] = conv(cur[k]).isoformat()
    for h in payload.get("hourly", []):
        if "dt" in h: h["dt_local"] = conv(h["dt"]).isoformat()
    for d in payload.get("daily", []):
        if "dt" in d: d["dt_local"] = conv(d["dt"]).isoformat()
        if "sunrise" in d: d["sunrise_local"] = conv(d["sunrise"]).isoformat()
        if "sunset" in d: d["sunset_local"] = conv(d["sunset"]).isoformat()
    return payload

