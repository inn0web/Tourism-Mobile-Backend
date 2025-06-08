from django.urls import path
from .views import (
    all_cities, get_user_feed,
    get_place_details, search_for_places
)

urlpatterns = [
    path('cities/', all_cities),
    path('feed/<int:city_id>/', get_user_feed),
    path('place/<str:place_id>/<str:tag>/', get_place_details),
    path('search/<int:city_id>/', search_for_places),
]