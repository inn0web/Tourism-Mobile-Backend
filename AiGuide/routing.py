# routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ai-guide/<str:city_name>/<int:user_id>/', consumers.EuroTripAiConsumer.as_asgi()),
    path('ai-guide/<str:city_name>/<int:user_id>/<str:thread_id>/', consumers.EuroTripAiConsumer.as_asgi()),
]
