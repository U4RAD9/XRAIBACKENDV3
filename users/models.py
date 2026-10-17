import uuid
import datetime
from django.db import models
from django.utils import timezone
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


def generate_consent_id():
    date_str = timezone.now().strftime('%Y%m%d')
    prefix = f"XRAI-DPDP-{date_str}-"
    existing_today = DPDPConsentLog.objects.filter(consent_id__startswith=prefix).values_list('consent_id', flat=True)
    max_seq = 0
    for cid in existing_today:
        try:
            suffix = cid.split('-')[-1]
            num = int(suffix)
            if num > max_seq:
                max_seq = num
        except (ValueError, IndexError):
            pass

    new_seq = max_seq + 1
    while DPDPConsentLog.objects.filter(consent_id=f"{prefix}{new_seq}").exists():
        new_seq += 1

    return f"{prefix}{new_seq}"


class DPDPConsentLog(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING_WITHDRAWAL', 'Pending Withdrawal'),
        ('WITHDRAWN', 'Withdrawn'),
        ('EXPIRED', 'Expired'),
    )

    consent_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique verifiable consent reference (e.g. XRAI-DPDP-YYYYMMDD-1)"
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='dpdp_consent_logs',
        help_text="Associated user account"
    )
    patient_number = models.CharField(
        max_length=30,
        db_index=True,
        help_text="Patient mobile number or unique contact identifier"
    )
    patient_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Assigned User ID / Patient ID"
    )
    full_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Full name of the data principal"
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email of the data principal"
    )
    shared_otp = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="The OTP verified by the user to authenticate and record consent"
    )
    notice_version = models.CharField(
        max_length=50,
        default='DPDP-1.0',
        help_text="Version of DPDP Notice and Consent Request"
    )
    notice_title = models.CharField(
        max_length=255,
        default='Digital Personal Data Protection Act, 2023 Consent Notice'
    )
    consent_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when the user accepted consent on the notice"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Server audit timestamp when record was persisted"
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        db_index=True
    )
    consented_purposes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Granular consent selections with full clause sentences"
    )
    consent_statement = models.TextField(
        default="I hereby consent to collection and processing of my data for availing Diagnostic Services and relevant services in the manner described in the notice here."
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra contextual audit metadata (channel, device, referrer, withdrawal history)"
    )

    class Meta:
        db_table = 'dpdp_consent_logs'
        verbose_name = 'DPDP Consent Log'
        verbose_name_plural = 'DPDP Consent Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consent_id']),
            models.Index(fields=['patient_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.consent_id} | {self.patient_number} | {self.status}"


class ConsultantExamResponse(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'In Progress / Draft'),
        ('SUBMITTED', 'Submitted'),
        ('EVALUATED', 'Evaluated'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='consultant_exam_responses',
        help_text="The consultant user who answered this exam packet"
    )
    exam_title = models.CharField(
        max_length=255,
        default="Clinical Case Examination Packet"
    )
    answers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full dictionary of all answers keyed by question/case identifiers"
    )
    current_view = models.CharField(
        max_length=50,
        default='intro',
        help_text="Last active view/tab of the consultant (e.g. intro, 1..13, closing)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    progress_stats = models.JSONField(
        default=dict,
        blank=True,
        help_text="Computed completion statistics (e.g. answered units, total units)"
    )
    compiled_summary = models.TextField(
        blank=True,
        null=True,
        help_text="Compiled human-readable text of all answers"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    last_saved_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'consultant_exam_responses'
        ordering = ['-last_saved_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_saved_at']),
        ]

    def __str__(self):
        return f"Consultant {self.user.user_name} - {self.exam_title} ({self.status})"

