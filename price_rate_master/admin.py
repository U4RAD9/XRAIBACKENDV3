from django.contrib import admin
from .models import PriceRateMaster, PriceRateMasterLocation

@admin.register(PriceRateMaster)
class PriceRateMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'visit_type', 'price', 'valid_from', 'valid_to', 'is_active')
    search_fields = ('service__service_name', 'visit_type')
    list_filter = ('visit_type', 'is_active')

@admin.register(PriceRateMasterLocation)
class PriceRateMasterLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'price_rate_master', 'location', 'custom_price')
    search_fields = ('price_rate_master__service__service_name', 'location__location_name')
    list_filter = ('location',)
