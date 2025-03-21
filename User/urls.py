from django.urls import path
from .views import (
    RegisterUser, LoginUser,
    MyTokenRefreshView, 
)
urlpatterns = [
    path('register/', RegisterUser),
    path('token/', LoginUser.as_view()),
    path('token/refresh/', MyTokenRefreshView.as_view()),
]