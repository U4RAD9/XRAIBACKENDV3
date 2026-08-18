from django.contrib import admin
from .models import Location

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = get_list_display(Location)
