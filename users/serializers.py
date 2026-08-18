from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    user_type_name = serializers.CharField(source='user_type.user_type_name', read_only=True)
    class Meta:
        model = User
        fields = '__all__'
