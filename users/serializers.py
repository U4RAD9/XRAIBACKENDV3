from rest_framework import serializers
from .models import User, UserLocationHistory, DPDPConsentLog

class UserSerializer(serializers.ModelSerializer):
    user_type_name = serializers.CharField(source='user_type.user_type_name', read_only=True)
    class Meta:
        model = User
        fields = '__all__'

class UserLocationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocationHistory
        fields = ['user', 'slot_booking', 'latitude', 'longitude', 'timestamp']

class DPDPConsentLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.user_name', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = DPDPConsentLog
        fields = '__all__'
