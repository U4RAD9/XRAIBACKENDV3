from django.conf import settings
import os
from django.contrib import admin
from django.utils.html import format_html
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import SlotBookingMaster, SlotBookingDetails, SlotBookingFile

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(SlotBookingMaster)
class SlotBookingMasterAdmin(admin.ModelAdmin):
    list_display = (
        'slot_booking_id',
        'get_patient_name',
        'get_phone_number',
        'get_services_booked',
        'location',
        'slot_booking_datetime',
        'payment_status',
        'status',
        'created_date',
    )
    search_fields = (
        'slot_booking_id',
        'patient_name',
        'phone_number',
        'alternate_mobile_number',
        'patient__patient_name',
        'patient__alternate_mobile_number',
        'user__user_name',
        'user__full_name',
        'user__mobile_number',
    )
    list_filter = ('status', 'payment_status', 'created_date', 'location')

    @admin.display(description='Patient Name', ordering='patient_name')
    def get_patient_name(self, obj):
        name = obj.patient_name
        if not name and obj.patient and obj.patient.patient_name:
            name = obj.patient.patient_name
        if not name and obj.user:
            name = obj.user.full_name or obj.user.user_name
        return name or '-'

    @admin.display(description='Phone Number', ordering='phone_number')
    def get_phone_number(self, obj):
        phone = (
            obj.phone_number or
            obj.alternate_mobile_number or
            (obj.patient.alternate_mobile_number if obj.patient else None) or
            (obj.user.mobile_number if obj.user else None)
        )
        return phone or '-'

    @admin.display(description='Services Booked')
    def get_services_booked(self, obj):
        services = list(obj.slotbookingdetails_set.values_list('service__service_name', flat=True))
        if services:
            return ", ".join([s for s in services if s])
        if obj.service_group:
            return obj.service_group.service_group_name
        return '-'

@admin.register(SlotBookingDetails)
class SlotBookingDetailsAdmin(admin.ModelAdmin):
    list_display = (
        'slot_booking_det_id',
        'get_booking_info',
        'service',
        'service_group',
        'price',
        'report_filename',
        'service_filename',
    )
    search_fields = (
        'slot_booking_det_id',
        'slot_booking__slot_booking_id',
        'slot_booking__patient_name',
        'slot_booking__phone_number',
        'slot_booking__patient__patient_name',
        'service__service_name',
        'report_filename',
        'service_filename',
    )
    list_filter = ('service_group', 'service')

    @admin.display(description='Booking Details', ordering='slot_booking__slot_booking_id')
    def get_booking_info(self, obj):
        if obj.slot_booking:
            sb = obj.slot_booking
            name = sb.patient_name
            if not name and sb.patient and sb.patient.patient_name:
                name = sb.patient.patient_name
            if not name and sb.user:
                name = sb.user.full_name or sb.user.user_name
            name = name or 'Patient'
            return f"Booking #{sb.slot_booking_id} ({name})"
        return "-"

@admin.register(SlotBookingFile)
class SlotBookingFileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_booking_id',
        'get_patient_name',
        'get_service_name',
        'file_type',
        'file_name',
        'get_file_link',
        'uploaded_on',
    )
    list_filter = ('file_type', 'file_extension', 'uploaded_on')
    search_fields = (
        'file_name',
        'file_type',
        'slot_booking_detail__slot_booking__slot_booking_id',
        'slot_booking_detail__slot_booking__patient_name',
        'slot_booking_detail__slot_booking__phone_number',
        'slot_booking_detail__service__service_name',
    )

    @admin.display(description='Booking ID', ordering='slot_booking_detail__slot_booking__slot_booking_id')
    def get_booking_id(self, obj):
        if obj.slot_booking_detail and obj.slot_booking_detail.slot_booking:
            return f"#{obj.slot_booking_detail.slot_booking.slot_booking_id}"
        return "-"

    @admin.display(description='Patient Name', ordering='slot_booking_detail__slot_booking__patient_name')
    def get_patient_name(self, obj):
        if obj.slot_booking_detail and obj.slot_booking_detail.slot_booking:
            sb = obj.slot_booking_detail.slot_booking
            name = sb.patient_name
            if not name and sb.patient and sb.patient.patient_name:
                name = sb.patient.patient_name
            if not name and sb.user:
                name = sb.user.full_name or sb.user.user_name
            return name or '-'
        return "-"

    @admin.display(description='Service / Test', ordering='slot_booking_detail__service__service_name')
    def get_service_name(self, obj):
        if obj.slot_booking_detail and obj.slot_booking_detail.service:
            return obj.slot_booking_detail.service.service_name
        return "-"

    @admin.display(description='View / Download')
    def get_file_link(self, obj):
        if obj.file_name:
            url = f"/media/{obj.file_name}"
            return format_html('<a href="{}" target="_blank" style="font-weight:600; color:#00acc1;">Open File &#8599;</a>', url)
        return "-"

@receiver(post_delete, sender=SlotBookingFile)
def delete_file_on_model_delete(sender, instance, **kwargs):
    if instance.file_name:
        file_path = os.path.join(settings.MEDIA_ROOT, instance.file_name)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
