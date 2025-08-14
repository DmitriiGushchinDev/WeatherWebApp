from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class City(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    region = models.CharField(max_length=255, blank=True, null=True)
    description = models.JSONField(blank=True, null=True)
    what_to_wear = models.JSONField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cities = models.ManyToManyField(City, related_name='profiles', blank=True)

    def __str__(self):
        return self.user.username