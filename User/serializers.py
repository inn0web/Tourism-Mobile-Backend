from rest_framework import serializers
from .models import User, Category, UserSearchHistory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'icon']

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    interests = CategorySerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'interests', 'language', 'notification_enabled', 'is_active', 'date_joined', 'profile_image']

    def get_profile_image(self, obj):
        return obj.user_profile_image()
    
class UserSearchHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSearchHistory
        fields = ['id', 'search', 'date']