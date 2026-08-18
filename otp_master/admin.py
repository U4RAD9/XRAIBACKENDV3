from django.contrib import admin
from .models import OtpMaster

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(OtpMaster)
class OtpMasterAdmin(admin.ModelAdmin):
    list_display = get_list_display(OtpMaster)
