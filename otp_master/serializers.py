from rest_framework import serializers
from .models import OtpMaster

class OtpMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtpMaster
        fields = '__all__'
