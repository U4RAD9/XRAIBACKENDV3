from django.db import models
from user_type.models import UserType

class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, db_column='user_type_id')
    user_name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    mpin = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user_name


class UserLocationHistory(models.Model):
    legacy_location_id = models.IntegerField(
        db_column="LocationID"
    )

    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="UserID",
        related_name="location_history",
    )

    longitude = models.FloatField()
    latitude = models.FloatField()

    timestamp = models.DateTimeField(
        db_column="TimeStamp"
    )

    slot_booking = models.ForeignKey(
        "bookings.SlotBookingMaster",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="SlotBookingID",
        related_name="location_history",
    )

    class Meta:
        db_table = "users_location_history"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["slot_booking"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.timestamp}"


class LegacyPermission(models.Model):
    permission_id = models.IntegerField(
        primary_key=True,
        db_column="ID"
    )

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column="User ID",
        related_name="legacy_permissions",
    )

    controller = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    action = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "legacy_permissions"

    def __str__(self):
        return f"{self.controller} - {self.action}"

class VisitType(models.Model):
    visit_type_id = models.IntegerField(
        primary_key=True,
        db_column="VISITTYPEID"
    )

    visit_type_name = models.CharField(
        max_length=100,
        db_column="VISITTYPENAME"
    )

    is_active = models.BooleanField(
        default=True,
        db_column="ISACTIVE"
    )

    trial353 = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        db_column="TRIAL353"
    )

    class Meta:
        db_table = "visit_type"

    def __str__(self):
        return self.visit_type_name
