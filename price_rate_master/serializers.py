from rest_framework import serializers
from .models import PriceRateMaster, PriceRateMasterLocation

class PriceRateMasterLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRateMasterLocation
        fields = '__all__'

class PriceRateMasterSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.service_name', read_only=True)
    service_group_name = serializers.CharField(source='service.service_group.service_group_name', read_only=True)
    
    class Meta:
        model = PriceRateMaster
        fields = '__all__'
