from rest_framework import serializers
from .models import Patient
from bookings.models import SlotBookingMaster

class PatientSerializer(serializers.ModelSerializer):
    booking_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'

    def get_booking_count(self, obj):
        return SlotBookingMaster.objects.filter(patient=obj).count()
