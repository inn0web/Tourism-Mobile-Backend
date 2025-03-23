from django.urls import path
from .views import (
    get_blogs_by_city, get_blog_detail
)

urlpatterns = [
    path('<str:city_name>/', get_blogs_by_city),
    path('detail/<int:blog_id>/', get_blog_detail),
]