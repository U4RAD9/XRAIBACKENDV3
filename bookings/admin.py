import os
from django.conf import settings
from django.contrib import admin
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import SlotBookingMaster, SlotBookingDetails, SlotBookingFile

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(SlotBookingMaster)
class SlotBookingMasterAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotBookingMaster)
    search_fields = ('slot_booking_id', 'phone_number')

@admin.register(SlotBookingDetails)
class SlotBookingDetailsAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotBookingDetails)
    search_fields = ('slot_booking_det_id', 'report_filename', 'service_filename')

@admin.register(SlotBookingFile)
class SlotBookingFileAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotBookingFile)
    search_fields = ('file_name', 'file_type', 'slot_booking_detail__slot_booking_det_id')
    list_filter = ('file_type', 'file_extension', 'uploaded_on')

@receiver(post_delete, sender=SlotBookingFile)
def delete_file_on_model_delete(sender, instance, **kwargs):
    if instance.file_name:
        file_path = os.path.join(settings.MEDIA_ROOT, instance.file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
