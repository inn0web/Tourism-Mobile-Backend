from rest_framework import serializers 
from .models import Advertisement

class AdvertisementSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Advertisement
        fields = ['title', 'subtitle', 'image', 'button_text', 'button_url']

    def get_image(self, obj):
        return obj.url