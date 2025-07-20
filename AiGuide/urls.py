from django.urls import path
from .import views

urlpatterns = [
    path('ai-test/', views.test_ai_guide),
    path('docs/ai/', views.WebSocketMockAPIView.as_view()),
    path('get-user-threads/', views.get_user_threads),
    path('get-thread-messages/<str:thread_id>/', views.get_thread_messages),
]