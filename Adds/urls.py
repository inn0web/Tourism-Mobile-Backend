from django.urls import path
from . import views

urlpatterns = [
    path('active-advertisements/', views.get_active_advertisements),
]