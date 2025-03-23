from django.urls import path
from .views import (
    GetCities, GetUserFeed
)

urlpatterns = [
    path('cities/', GetCities),
    # path('feed/', GetUserFeed),
]