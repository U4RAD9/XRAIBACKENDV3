from rest_framework import viewsets
from .models import ServiceGroup
from .serializers import ServiceGroupSerializer

class ServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer
