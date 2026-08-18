from django.contrib import admin
from .models import OfferMaster

@admin.register(OfferMaster)
class OfferMasterAdmin(admin.ModelAdmin):
    list_display = [f.name for f in OfferMaster._meta.fields]
