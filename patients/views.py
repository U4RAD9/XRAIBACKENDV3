from rest_framework import viewsets, filters
from webportal_core.pagination import StandardResultsSetPagination
from .models import Patient
from .serializers import PatientSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-patient_id')
    serializer_class = PatientSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['patient_name', 'first_name', 'last_name', 'alternate_mobile_number', 'email', 'ref_no']

    def get_queryset(self):
        queryset = Patient.objects.all().order_by('-patient_id')
        user_info = getattr(self.request, 'user_info', {})
        user_type = user_info.get('UserType', '').lower()
        logged_in_user_id = user_info.get('UserID')

        if user_type == 'partner':
            queryset = queryset.filter(user_id=logged_in_user_id)
        
        # Keep query param filter for admin/other usage
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset

    def perform_create(self, serializer):
        user_info = getattr(self.request, 'user_info', {})
        user_type = user_info.get('UserType', '').lower()
        logged_in_user_id = user_info.get('UserID')

        if user_type == 'partner' and logged_in_user_id:
            serializer.save(user_id=logged_in_user_id)
            return

        user_id_val = self.request.data.get('user_id')
        try:
            if user_id_val and str(user_id_val).lower() not in ['null', 'undefined', '']:
                serializer.save(user_id=int(user_id_val))
            else:
                serializer.save()
        except Exception:
            serializer.save()
