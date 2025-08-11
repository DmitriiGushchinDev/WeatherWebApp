from django.contrib import admin
from .models import City, Profile
from django.contrib.auth.admin import UserAdmin
# Register your models here.

class CityAdmin(admin.ModelAdmin):
    model = City
    list_display = ('name', 'country', 'latitude', 'longitude', 'region')


admin.site.register(City, CityAdmin)
admin.site.register(Profile)
