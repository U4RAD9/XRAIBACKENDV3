from rest_framework import serializers
from .models import User, UserLocationHistory, DPDPConsentLog, TechnicianOnboarding

class UserSerializer(serializers.ModelSerializer):
    user_type_name = serializers.CharField(source='user_type.user_type_name', read_only=True)
    class Meta:
        model = User
        fields = [
            'id', 'user_type', 'user_type_name', 'user_name', 'mobile_number',
            'is_active', 'added_date', 'updated_date', 'full_name',
            'email', 'gender', 'age', 'first_name', 'last_name',
            'password', 'mpin'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'mpin': {'write_only': True, 'required': False}
        }

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


class TechnicianOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianOnboarding
        fields = '__all__'
