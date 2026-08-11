from rest_framework import serializers
from .models import UserType, User, Permission, UsersLocation, OtpMaster

class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

class UsersLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersLocation
        fields = '__all__'

class OtpMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtpMaster
        fields = '__all__'
