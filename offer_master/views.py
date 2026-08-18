from rest_framework import viewsets
from .models import OfferMaster
from .serializers import OfferMasterSerializer

class OfferMasterViewSet(viewsets.ModelViewSet):
    queryset = OfferMaster.objects.all().order_by('-id')
    serializer_class = OfferMasterSerializer
