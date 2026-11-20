from django.contrib import admin
from .models import SlotMaster

@admin.register(SlotMaster)
class SlotMasterAdmin(admin.ModelAdmin):
    list_display = ('slot_id', 'slot_name', 'is_active')
    search_fields = ('slot_name', 'slot_id')
    list_filter = ('is_active',)
