from django.contrib import admin
from .models import UserType

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = get_list_display(UserType)
