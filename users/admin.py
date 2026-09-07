from django.contrib import admin
from .models import User
from .models import LegacyPermission, VisitType, UserLocationHistory

def get_list_display(model):
    return [field.name for field in model._meta.fields]

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = get_list_display(User)

admin.site.register(LegacyPermission)
admin.site.register(VisitType)
admin.site.register(UserLocationHistory)
