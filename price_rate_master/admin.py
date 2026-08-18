from django.contrib import admin
from .models import PriceRateMaster, PriceRateMasterLocation

@admin.register(PriceRateMaster)
class PriceRateMasterAdmin(admin.ModelAdmin):
    list_display = [f.name for f in PriceRateMaster._meta.fields]

@admin.register(PriceRateMasterLocation)
class PriceRateMasterLocationAdmin(admin.ModelAdmin):
    list_display = [f.name for f in PriceRateMasterLocation._meta.fields]
