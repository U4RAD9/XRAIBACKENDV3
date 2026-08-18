from rest_framework import viewsets
from .models import OtpMaster
from .serializers import OtpMasterSerializer

class OtpMasterViewSet(viewsets.ModelViewSet):
    queryset = OtpMaster.objects.all()
    serializer_class = OtpMasterSerializer
