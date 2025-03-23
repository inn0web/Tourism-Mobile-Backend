from rest_framework import serializers
from .models import Blog, BlogImage

class BlogListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'title', 'thumbnail', 'city', 'created_at']

    def get_thumbnail(self, obj):
        return obj.thumbnail.url
    
    def get_city(self, obj):

        return obj.city.name if obj.city else ""
    
class BlogDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField() 

    class Meta:
        model = Blog
        fields = ['id', 'title', 'thumbnail', 'city', 'content', 'images', 'created_at']

    def get_thumbnail(self, obj):
        return obj.thumbnail.url if obj.thumbnail else None
    
    def get_images(self, obj):
        
        return obj.get_images()
    
    def get_city(self, obj):

        return obj.city.name if obj.city else ""