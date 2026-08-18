from rest_framework import viewsets
from .models import PriceRateMaster, PriceRateMasterLocation
from .serializers import PriceRateMasterSerializer, PriceRateMasterLocationSerializer

class PriceRateMasterViewSet(viewsets.ModelViewSet):
    queryset = PriceRateMaster.objects.all().order_by('-id')
    serializer_class = PriceRateMasterSerializer

class PriceRateMasterLocationViewSet(viewsets.ModelViewSet):
    queryset = PriceRateMasterLocation.objects.all().order_by('-id')
    serializer_class = PriceRateMasterLocationSerializer
