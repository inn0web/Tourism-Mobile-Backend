from django.urls import path
from .views import (
    GetCities,
)

urlpatterns = [
    path('cities/', GetCities),
]