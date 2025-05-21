from rest_framework import serializers 
from .models import Advertisement

class AdvertisementSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    second_image = serializers.SerializerMethodField()

    
    class Meta:
        model = Advertisement
        fields = ['title', 'subtitle', 'image', 'second_image', 'button_text', 'button_url']

    def get_image(self, obj):
        return obj.image.url
    
    def get_second_image(self, obj):
        return obj.second_image.url