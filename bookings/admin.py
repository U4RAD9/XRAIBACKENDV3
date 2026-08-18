from django.contrib import admin
from .models import SlotBookingMaster, SlotBookingDetails

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(SlotBookingMaster)
class SlotBookingMasterAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotBookingMaster)

@admin.register(SlotBookingDetails)
class SlotBookingDetailsAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotBookingDetails)
