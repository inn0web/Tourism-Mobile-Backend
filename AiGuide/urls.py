from django.urls import path
from .import views

urlpatterns = [
    path('ai-test/', views.test_ai_guide)
]