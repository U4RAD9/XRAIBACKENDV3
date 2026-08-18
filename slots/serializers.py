from rest_framework import serializers
from .models import SlotMaster

class SlotMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotMaster
        fields = '__all__'
