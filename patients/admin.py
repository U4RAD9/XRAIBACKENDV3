from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'patient_name', 'alternate_mobile_number', 'email', 'age', 'gender', 'added_date')
    search_fields = ('patient_id', 'patient_name', 'alternate_mobile_number', 'email')
    list_filter = ('gender', 'added_date')
