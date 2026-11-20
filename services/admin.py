from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'service_name', 'service_group', 'is_active', 'added_date')
    search_fields = ('service_id', 'service_name', 'service_group__service_group_name')
    list_filter = ('service_group', 'is_active')
