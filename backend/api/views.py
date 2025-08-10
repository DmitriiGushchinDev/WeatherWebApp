from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from cities.models import City
from cities.serializers import CitySerializer

