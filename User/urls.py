from django.urls import path
from .views import (
    RegisterUser, LoginUser
)
urlpatterns = [
    path('register/', RegisterUser),
    path('login/', LoginUser.as_view()),
]