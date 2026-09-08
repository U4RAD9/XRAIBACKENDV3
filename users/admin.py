from django.contrib import admin
from .models import (
    User,
    LegacyPermission,
    VisitType,
    UserLocationHistory,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_name",
        "full_name",
        "email",
        "mobile_number",
        "user_type",
        "is_active",
        "added_date",
        "updated_date",
    )

    list_filter = (
        "user_type",
        "is_active",
        "gender",
    )

    search_fields = (
        "user_name",
        "full_name",
        "email",
        "mobile_number",
    )

    ordering = ("-id",)


@admin.register(UserLocationHistory)
class UserLocationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "legacy_location_id",
        "longitude",
        "latitude",
        "timestamp",
        "slot_booking",
    )

    list_filter = (
        "timestamp",
    )

    search_fields = (
        "user__user_name",
        "user__full_name",
        "legacy_location_id",
    )

    ordering = ("-timestamp",)


@admin.register(LegacyPermission)
class LegacyPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "permission_id",
        "user",
        "controller",
        "action",
    )

    list_filter = (
        "controller",
        "action",
    )

    search_fields = (
        "controller",
        "action",
        "user__user_name",
        "user__full_name",
    )

    ordering = ("permission_id",)


@admin.register(VisitType)
class VisitTypeAdmin(admin.ModelAdmin):
    list_display = (
        "visit_type_id",
        "visit_type_name",
        "is_active",
        "trial353",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "visit_type_name",
    )

    ordering = ("visit_type_id",)