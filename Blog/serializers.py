from rest_framework import serializers
from .models import Blog, BlogImage
from django.utils.timezone import localtime

class BlogListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'title', 'thumbnail', 'read_time', 'city', 'created_at']

    def get_thumbnail(self, obj):
        return obj.thumbnail.url
    
    def get_city(self, obj):
        return obj.city.name if obj.city else ""
    
    def get_created_at(self, obj):
        return localtime(obj.created_at).strftime('%B %d, %Y %I:%M %p')  
    
class BlogDetailSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField() 
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'title', 'thumbnail', 'read_time', 'city', 'content', 'images', 'created_at']

    def get_thumbnail(self, obj):
        return obj.thumbnail.url if obj.thumbnail else None
    
    def get_images(self, obj):
        return obj.get_images()
    
    def get_city(self, obj):
        return obj.city.name if obj.city else ""
    
    def get_created_at(self, obj):
        return localtime(obj.created_at).strftime('%B %d, %Y %I:%M %p')  