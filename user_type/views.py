from rest_framework import viewsets
from .models import UserType
from .serializers import UserTypeSerializer

class UserTypeViewSet(viewsets.ModelViewSet):
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer
