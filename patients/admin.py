from django.contrib import admin
from .models import Patient

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = get_list_display(Patient)
