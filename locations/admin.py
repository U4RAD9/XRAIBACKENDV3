from django.contrib import admin
from .models import Location

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('location_id', 'location_name', 'is_active', 'added_date')
    search_fields = ('location_name', 'location_id')
    list_filter = ('is_active',)
