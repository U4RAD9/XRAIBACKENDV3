from django.contrib import admin
from .models import ServiceGroup

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ('service_group_id', 'service_group_name', 'is_active', 'added_date')
    search_fields = ('service_group_name', 'service_group_id')
    list_filter = ('is_active',)
