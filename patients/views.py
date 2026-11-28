from rest_framework import viewsets, filters
from rest_framework.exceptions import PermissionDenied
from webportal_core.pagination import StandardResultsSetPagination
from .models import Patient
from .serializers import PatientSerializer
from bookings.models import SlotBookingMaster

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-patient_id')
    serializer_class = PatientSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['patient_name', 'first_name', 'last_name', 'alternate_mobile_number', 'email', 'ref_no']

    def get_queryset(self):
        queryset = Patient.objects.all().order_by('-patient_id')
        user_info = getattr(self.request, 'user_info', {})
        user_type = str(user_info.get('UserType', '')).strip().lower()
        logged_in_user_id = user_info.get('UserID')

        # Patients and Partners are strictly locked to their own patient records
        if user_type in ['patient', 'partner']:
            if logged_in_user_id:
                return queryset.filter(user_id=logged_in_user_id)
            return queryset.none()
        
        # Technician can only see patients if linked to their assigned bookings
        if user_type == 'technician':
            if logged_in_user_id:
                return queryset.filter(slotbookingmaster__service_provider_id=logged_in_user_id).distinct()
            return queryset.none()

        # Admins / SuperAdmins / Doctors can view all, or filter by query param
        if user_type in ['admin', 'superadmin', 'doctor', 'consultant admin', 'consultant_admin', 'technician admin', 'technician_admin']:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            return queryset

        # Fallback for any other non-admin role: strictly own records
        if logged_in_user_id:
            return queryset.filter(user_id=logged_in_user_id)
        return queryset.none()

    def perform_create(self, serializer):
        user_info = getattr(self.request, 'user_info', {})
        user_type = str(user_info.get('UserType', '')).strip().lower()
        logged_in_user_id = user_info.get('UserID')

        if user_type in ['partner', 'patient'] and logged_in_user_id:
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

    def perform_update(self, serializer):
        user_info = getattr(self.request, 'user_info', {})
        user_type = str(user_info.get('UserType', '')).strip().lower()
        logged_in_user_id = user_info.get('UserID')

        # Enforce that patients/partners can only update their own records
        if user_type in ['patient', 'partner'] and logged_in_user_id:
            instance = self.get_object()
            if instance.user_id != logged_in_user_id:
                raise PermissionDenied("You do not have permission to modify this patient.")

        patient = serializer.save()
        # Update associated bookings with new patient data
        SlotBookingMaster.objects.filter(patient=patient).update(
            patient_name=patient.patient_name,
            age=patient.age,
            weight=patient.weight,
            gender=patient.gender,
            address=patient.address,
            alternate_mobile_number=patient.alternate_mobile_number,
            email=patient.email
        )

    def perform_destroy(self, instance):
        user_info = getattr(self.request, 'user_info', {})
        user_type = str(user_info.get('UserType', '')).strip().lower()

        # Only administrators can delete patient records
        if user_type not in ['admin', 'superadmin']:
            raise PermissionDenied("Only administrators are permitted to delete patient records.")

        from users.models import UserLocationHistory
        bookings = SlotBookingMaster.objects.filter(patient=instance)
        
        # Delete all technician tracking location points associated with these bookings
        UserLocationHistory.objects.filter(slot_booking__in=bookings).delete()
        
        # Delete all bookings (cascade will delete SlotBookingDetails and SlotBookingFiles)
        bookings.delete()
        
        # Finally delete the patient
        instance.delete()
