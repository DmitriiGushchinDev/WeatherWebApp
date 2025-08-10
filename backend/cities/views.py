from django.shortcuts import render
from .models import City
# Create your views here.
def cities_list(request):
    cities = City.objects.all()
    return render(request, 'cities/city_list.html', {'cities': cities})


def geolocation(request):
    cities = City.objects.all()
    return render(request, 'cities/geolocation.html',{'cities': cities})
