from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import SlotMaster
from .serializers import SlotMasterSerializer

class SlotMasterViewSet(viewsets.ModelViewSet):
    queryset = SlotMaster.objects.all()
    serializer_class = SlotMasterSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def get_slots(request):
    date = request.query_params.get('date')
    # In a real app we'd filter by date, but we just return all active slots for now to match the UI behavior
    slots = SlotMaster.objects.filter(is_active=True).values('slot_id', 'slot_name')
    return Response(list(slots), status=status.HTTP_200_OK)
