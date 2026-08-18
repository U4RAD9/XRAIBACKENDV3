from django.contrib import admin
from .models import ServiceGroup

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = get_list_display(ServiceGroup)
