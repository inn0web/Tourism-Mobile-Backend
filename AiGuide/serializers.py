from rest_framework import serializers
from .models import Thread, ThreadMessage

class WebSocketPlaceMessageSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Description of the place.")
    photos = serializers.ListField(
        child=serializers.URLField(),
        help_text="List of photo URLs related to the place."
    )

class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ['id', 'thread_name', 'thread_id', 'created_when']

class ThreadMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThreadMessage
        fields = ['is_user_message', 'is_ai_message', 'message_content', 'sent_when']