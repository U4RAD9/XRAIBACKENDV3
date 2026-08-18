from rest_framework import serializers
from .models import SlotBookingMaster, SlotBookingDetails

class SlotBookingMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBookingMaster
        fields = '__all__'

class SlotBookingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBookingDetails
        fields = '__all__'
