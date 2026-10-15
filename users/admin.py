import json
from django import forms
from django.contrib import admin
from .models import (
    User,
    LegacyPermission,
    VisitType,
    UserLocationHistory,
    DPDPConsentLog,
)


class PrettyJSONWidget(forms.Textarea):
    def format_value(self, value):
        if value is None or value == "":
            return ""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                return value
        return json.dumps(value, indent=2, ensure_ascii=False)


class DPDPConsentLogForm(forms.ModelForm):
    class Meta:
        model = DPDPConsentLog
        fields = '__all__'
        widgets = {
            'consented_purposes': PrettyJSONWidget(attrs={
                'rows': 18,
                'style': 'font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; width: 100%; white-space: pre-wrap; padding: 10px; border-radius: 6px;'
            }),
            'metadata': PrettyJSONWidget(attrs={
                'rows': 6,
                'style': 'font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; width: 100%; white-space: pre-wrap; padding: 10px; border-radius: 6px;'
            }),
        }


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


@admin.register(DPDPConsentLog)
class DPDPConsentLogAdmin(admin.ModelAdmin):
    form = DPDPConsentLogForm
    list_display = (
        "consent_id",
        "patient_id",
        "patient_number",
        "full_name",
        "shared_otp",
        "status",
        "notice_version",
        "consent_timestamp",
        "created_at",
    )
    list_filter = (
        "status",
        "notice_version",
        "created_at",
    )
    search_fields = (
        "consent_id",
        "patient_number",
        "patient_id",
        "full_name",
        "email",
        "shared_otp",
    )
    readonly_fields = (
        "consent_id",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)