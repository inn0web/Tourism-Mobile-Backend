from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'is_active', 'date_joined', 'profile_image']

    def get_profile_image(self, obj):
        return obj.user_profile_image()