from rest_framework import serializers
from .models import Location, ServiceGroup, Service, LocationServiceMapping, VisitTypeMaster, PriceRateMaster, PriceRateMasterLocations, OfferMaster, OfferLocations, OfferServiceGroups, SlotMaster, Patient, SlotBookingMaster, SlotBookingDetails, SlotBookingMasterRemarks, ReportFilesDetails, ServiceFilesDetails

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class ServiceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceGroup
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class LocationServiceMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationServiceMapping
        fields = '__all__'

class VisitTypeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitTypeMaster
        fields = '__all__'

class PriceRateMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRateMaster
        fields = '__all__'

class PriceRateMasterLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRateMasterLocations
        fields = '__all__'

class OfferMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferMaster
        fields = '__all__'

class OfferLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferLocations
        fields = '__all__'

class OfferServiceGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferServiceGroups
        fields = '__all__'

class SlotMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotMaster
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class SlotBookingMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBookingMaster
        fields = '__all__'

class SlotBookingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBookingDetails
        fields = '__all__'

class SlotBookingMasterRemarksSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBookingMasterRemarks
        fields = '__all__'

class ReportFilesDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportFilesDetails
        fields = '__all__'

class ServiceFilesDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFilesDetails
        fields = '__all__'
