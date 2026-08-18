from rest_framework import serializers
from .models import ServiceGroup

class ServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGroup
        fields = '__all__'
