from rest_framework import serializers
from .models import OfferMaster

class OfferMasterSerializer(serializers.ModelSerializer):
    service_group_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    user_type_name = serializers.SerializerMethodField()

    def get_service_group_name(self, obj):
        return ", ".join([sg.service_group_name for sg in obj.service_group.all() if sg.service_group_name])
        
    def get_location_name(self, obj):
        return ", ".join([loc.location_name for loc in obj.location.all() if loc.location_name])
        
    def get_user_type_name(self, obj):
        return ", ".join([ut.user_type_name for ut in obj.user_type.all() if ut.user_type_name])

    class Meta:
        model = OfferMaster
        fields = '__all__'
