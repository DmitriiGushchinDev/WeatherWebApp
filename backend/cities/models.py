from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    region = models.CharField(max_length=255)


    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cities = models.ManyToManyField(City, related_name='profiles')

    def __str__(self):
        return self.user.username