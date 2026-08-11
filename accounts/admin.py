from django.contrib import admin
from .models import UserType, User, Permission, UsersLocation, OtpMaster

admin.site.register(UserType)
admin.site.register(User)
admin.site.register(Permission)
admin.site.register(UsersLocation)
admin.site.register(OtpMaster)
