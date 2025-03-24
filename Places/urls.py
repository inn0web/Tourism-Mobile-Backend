from django.urls import path
from .views import (
    all_cities, get_user_feed
)

urlpatterns = [
    path('cities/', all_cities),
    # path('feed/', get_user_feed),
]