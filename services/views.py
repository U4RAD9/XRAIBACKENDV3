from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Service
from .serializers import ServiceSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def get_services_by_group(request):
    group_id = request.query_params.get('group_id')
    if not group_id:
        return Response([], status=status.HTTP_200_OK)
    
    services = Service.objects.filter(service_group_id=group_id, is_active=True).values('service_id', 'service_name')
    return Response(list(services), status=status.HTTP_200_OK)
