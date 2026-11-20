from django.contrib import admin
from .models import OfferMaster

@admin.register(OfferMaster)
class OfferMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'offer_name', 'discount', 'discount_type', 'effective_from', 'effective_to', 'is_active')
    search_fields = ('offer_name', 'discount_type')
    list_filter = ('discount_type', 'is_active')
