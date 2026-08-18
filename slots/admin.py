from django.contrib import admin
from .models import SlotMaster

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(SlotMaster)
class SlotMasterAdmin(admin.ModelAdmin):
    list_display = get_list_display(SlotMaster)
