from rest_framework import viewsets, filters
from webportal_core.pagination import StandardResultsSetPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from django.conf import settings

class OTPRateThrottle(AnonRateThrottle):
    scope = 'otp_requests'

import random
import traceback
import requests
import threading
import csv
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

def send_sms_background(url, headers, payload):
    try:
        requests.post(url, headers=headers, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending SMS: {e}")

from user_type.models import UserType
from .serializers import UserSerializer, UserLocationHistorySerializer, DPDPConsentLogSerializer, TechnicianOnboardingSerializer
from otp_master.models import OtpMaster
from .models import User, UserLocationHistory, DPDPConsentLog, generate_consent_id, ConsultantExamResponse, TechnicianOnboarding

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['user_name', 'mobile_number', 'full_name', 'email']

    def get_queryset(self):
        qs = super().get_queryset()
        user_info = getattr(self.request, 'user_info', {})
        u_type = (user_info.get('UserType') or '').lower()
        if u_type in ['consultant admin', 'consultant_admin', 'consultantadmin']:
            # Consultant Admin strictly sees Consultant and Consultant Admin user accounts
            qs = qs.filter(user_type__user_type_name__in=['Consultant', 'Consultant Admin'])
        user_type_param = self.request.query_params.get('user_type')
        if user_type_param:
            qs = qs.filter(user_type__user_type_name__iexact=user_type_param)
        return qs

    def _prepare_data(self, data):
        data = data.copy()
        user_type_name = data.pop('userType', None)
        if type(user_type_name) is list:
            user_type_name = user_type_name[0]
            
        if user_type_name:
            user_type = UserType.objects.filter(user_type_name=user_type_name).first()
            if not user_type:
                user_type = UserType.objects.create(user_type_name=user_type_name)
            data['user_type'] = user_type.user_type_id
            
        if 'password' in data:
            data['mpin'] = data['password']
        if 'username' in data:
            data['user_name'] = data['username']
        if 'fullName' in data and data['fullName']:
            data['full_name'] = data['fullName']
        elif 'full_name' not in data and 'username' in data:
            data['full_name'] = data['username']
        if 'mobile' in data:
            data['mobile_number'] = data['mobile']
            
        return data

    def create(self, request, *args, **kwargs):
        user_info = getattr(request, 'user_info', {})
        u_type = (user_info.get('UserType') or '').lower()
        if u_type in ['consultant admin', 'consultant_admin', 'consultantadmin']:
            req_type = request.data.get('userType')
            if req_type and req_type not in ['Consultant', 'Consultant Admin']:
                return Response({"Success": False, "Message": "Consultant Admin can only manage Consultant accounts."}, status=status.HTTP_403_FORBIDDEN)

        data = self._prepare_data(request.data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = self._prepare_data(request.data)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

@api_view(['POST'])
@throttle_classes([OTPRateThrottle])
@permission_classes([AllowAny])
def send_otp(request):
    mobile = request.data.get('mobile')
    if not mobile:
        return Response({"StatusCode": False, "Message": "Mobile number required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(mobile_number=mobile).exists():
        return Response({"StatusCode": False, "Message": "User with this mobile number already exist."}, status=status.HTTP_200_OK)
    
    otp_val = str(random.randint(100000, 999999))
    try:
        OtpMaster.objects.create(otp=otp_val, mobile=mobile, otp_datetime=timezone.now())
        
        # Send SMS via Fast2SMS asynchronously
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": settings.FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "route": "dlt",
            "sender_id": "XRAIHD",
            "message": "204046",
            "variables_values": otp_val,
            "numbers": mobile
        }
        threading.Thread(target=send_sms_background, args=(url, headers, payload)).start()
        
        return Response({"StatusCode": True, "Message": f"OTP has been sent to {mobile}. Please verify your OTP to complete registration."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"StatusCode": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    mobile = request.data.get('mobile')
    otp = request.data.get('otp')
    if not mobile or not otp:
        return Response(False, status=status.HTTP_200_OK)
    
    latest_otp = OtpMaster.objects.filter(mobile=mobile).order_by('-otp_id').first()
    if latest_otp and latest_otp.otp == otp:
        return Response(True, status=status.HTTP_200_OK)
    
    return Response(False, status=status.HTTP_200_OK)

CLAUSE_DESCRIPTIONS = {
    'a': 'I have read and understood this Notice and Request for Consent.',
    'b': 'I consent to U4RAD Technologies and its brand XRAi Digital collecting and Processing my personal and health data for the purposes in Section 2, except research and internal marketing, which need my separate consent below.',
    'c': 'I understand that if my test is sponsored by an employer or insurer, my result will be shared with that sponsor.',
    'd': 'I am 18 or older, or I am the parent / guardian giving consent on behalf of a minor.',
    'e': 'I agree to receive service communications (results, appointment updates) by phone, SMS, email or WhatsApp.',
    'f': 'Research: my de-identified data may be used for research and to improve clinical outcomes and our data models.',
    'g': 'Offers: XRAi Digital may use my data only for internal marketing of test discounts and offers. My data will NOT be shared with any third party for marketing.',
    'h': 'Longer retention: my reports and images may be kept beyond the period required by law, so doctors can compare my future tests with earlier ones.',
}

def format_consented_purposes(consent_record):
    required_in = consent_record.get('required', {}) if isinstance(consent_record, dict) else {}
    optional_in = consent_record.get('optional', {}) if isinstance(consent_record, dict) else {}

    required_out = {}
    for k in ['a', 'b', 'c', 'd', 'e']:
        desc = CLAUSE_DESCRIPTIONS[k]
        val = required_in.get(k) if k in required_in else required_in.get(desc, True)
        required_out[desc] = bool(val)

    optional_out = {}
    for k in ['f', 'g', 'h']:
        desc = CLAUSE_DESCRIPTIONS[k]
        val = optional_in.get(k) if k in optional_in else optional_in.get(desc, True)
        optional_out[desc] = bool(val)

    return {
        'required': required_out,
        'optional': optional_out
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    try:
        mobile = request.data.get('MobileNumber')
        mpin = request.data.get('MPIN')
        full_name = request.data.get('FullName')
        email = request.data.get('Email')
        gender = request.data.get('Gender')
        age = request.data.get('Age')
        otp = request.data.get('otp')
        consent_record = request.data.get('consentRecord', {})

        if User.objects.filter(mobile_number=mobile).exists():
            return Response({"Success": False, "Message": "User already exists"}, status=status.HTTP_200_OK)

        user_type = UserType.objects.filter(user_type_name="Patient").first()
        if not user_type:
            user_type = UserType.objects.create(user_type_name="Patient")

        user = User.objects.create(
            user_type=user_type,
            user_name=mobile,
            mobile_number=mobile,
            password=mpin,
            mpin=mpin,
            full_name=full_name,
            email=email,
            gender=gender,
            age=age
        )

        # Record DPDP Consent Audit Trail
        consent_id = None
        try:
            shared_otp_val = otp
            if not shared_otp_val:
                latest_otp_obj = OtpMaster.objects.filter(mobile=mobile).order_by('-otp_id').first()
                if latest_otp_obj:
                    shared_otp_val = latest_otp_obj.otp

            consent_ts = timezone.now()
            if isinstance(consent_record, dict) and consent_record.get('timestamp'):
                try:
                    from django.utils.dateparse import parse_datetime
                    parsed = parse_datetime(consent_record.get('timestamp'))
                    if parsed:
                        consent_ts = parsed
                except Exception:
                    pass

            notice_version = consent_record.get('noticeVersion', 'DPDP-1.0') if isinstance(consent_record, dict) else 'DPDP-1.0'
            consented_purposes = format_consented_purposes(consent_record)

            consent_log = DPDPConsentLog.objects.create(
                consent_id=generate_consent_id(),
                user=user,
                patient_id=user.id,
                patient_number=mobile,
                full_name=full_name,
                email=email,
                shared_otp=shared_otp_val,
                notice_version=notice_version,
                notice_title='Digital Personal Data Protection Act, 2023 Consent Notice',
                consent_timestamp=consent_ts,
                status='ACTIVE',
                consented_purposes=consented_purposes,
                consent_statement="I hereby consent to collection and processing of my data for availing Diagnostic Services and relevant services in the manner described in the notice here.",
                metadata={
                    'channel': 'web_patient_registration',
                    'gender': gender,
                    'age': age
                }
            )
            consent_id = consent_log.consent_id
        except Exception as consent_err:
            print(f"Error saving DPDP consent log: {consent_err}")

        return Response({
            "Success": True, 
            "Message": "User registered successfully",
            "ConsentID": consent_id
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def authenticate_user(request):
    mobile_or_username = request.data.get('MobileNumber') or request.data.get('username')
    mpin = request.data.get('MPIN') or request.data.get('password')

    if not mobile_or_username or not mpin:
        return Response({"Success": False, "message": "Username / Mobile number and password are required."}, status=status.HTTP_200_OK)

    try:
        from django.db import models
        user = User.objects.filter(models.Q(mobile_number=mobile_or_username) | models.Q(user_name=mobile_or_username)).first()
        
        if not user:
            return Response({"Success": False, "message": "Mobile number or username is not registered."}, status=status.HTTP_200_OK)

        if user.mpin == mpin or user.password == mpin:
            from django.core import signing
            token_payload = {
                "UserID": user.id,
                "UserType": user.user_type.user_type_name
            }
            auth_token = signing.dumps(token_payload)

            return Response({
                "Success": True, 
                "message": "User has been logged in successfully.",
                "Token": auth_token,
                "UserType": user.user_type.user_type_name,
                "UserID": user.id,
                "UserName": user.user_name,
                "FullName": user.full_name or user.user_name,
                "Age": user.age,
                "Gender": user.gender,
                "MobileNumber": user.mobile_number
            }, status=status.HTTP_200_OK)
        else:
            return Response({"Success": False, "message": "Invalid password or MPIN."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "message": str(e)}, status=status.HTTP_200_OK)

@api_view(['POST'])
@throttle_classes([OTPRateThrottle])
@permission_classes([AllowAny])
def forget_mpin(request):
    mobile = request.data.get('mobile')
    if not mobile:
        return Response({"StatusCode": False, "Message": "Mobile number required"}, status=status.HTTP_400_BAD_REQUEST)
    
    if not User.objects.filter(mobile_number=mobile).exists():
        return Response({"StatusCode": False, "Message": "User does not exist with this mobile number."}, status=status.HTTP_200_OK)
    
    otp_val = str(random.randint(100000, 999999))
    try:
        OtpMaster.objects.create(otp=otp_val, mobile=mobile, otp_datetime=timezone.now())
        
        # Send SMS via Fast2SMS asynchronously
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": settings.FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "route": "dlt",
            "sender_id": "XRAIHD",
            "message": "204045",
            "variables_values": otp_val,
            "numbers": mobile
        }
        threading.Thread(target=send_sms_background, args=(url, headers, payload)).start()

        return Response({"StatusCode": True, "Message": "OTP has been sent to your registered mobile number."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"StatusCode": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_visitor_mpin(request):
    mobile = request.query_params.get('mobile')
    if not mobile:
        return Response({"StatusCode": False, "MPin": ""}, status=status.HTTP_200_OK)
    
    try:
        user = User.objects.filter(mobile_number=mobile).first()
        if user:
            return Response({"StatusCode": True, "MPin": user.mpin}, status=status.HTTP_200_OK)
        else:
            return Response({"StatusCode": False, "MPin": ""}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"StatusCode": False, "MPin": ""}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def employee_login(request):
    username = request.data.get('Username')
    password = request.data.get('Password')

    if not username or not password:
        return Response({"Success": False, "message": "Username and Password required."}, status=status.HTTP_200_OK)

    try:
        user = User.objects.get(user_name=username, password=password)
        return Response({
            "Success": True, 
            "message": "Logged in successfully.",
            "UserType": user.user_type.user_type_name,
            "UserID": user.id,
            "UserName": user.user_name
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"Success": False, "message": "Invalid username or password."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "message": str(e)}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_password(request):
    mobile = request.data.get('mobile')
    new_password = request.data.get('new_password')
    
    if not mobile or not new_password:
        return Response({"Success": False, "Message": "Mobile and New Password are required."}, status=status.HTTP_200_OK)
        
    try:
        user = User.objects.filter(mobile_number=mobile).first()
        if not user:
            return Response({"Success": False, "Message": "User not found."}, status=status.HTTP_200_OK)
        
        user.password = new_password
        user.mpin = new_password
        user.save()
        return Response({"Success": True, "Message": "Password updated successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny]) # Adjust if needing auth
def tracking_api(request):
    from bookings.models import SlotBookingMaster

    if request.method == 'POST':
        # Check if booking is already Completed. If completed, lock and reject updates permanently.
        slot_booking_id = request.data.get('slot_booking')
        if slot_booking_id:
            try:
                booking = SlotBookingMaster.objects.filter(slot_booking_id=slot_booking_id).first()
                if booking and str(booking.status or '').strip().lower() == 'completed':
                    return Response({
                        "Success": False,
                        "Message": "Tracking is stopped for this case because it is already marked as Completed.",
                        "is_completed": True
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception:
                pass

        # Technician pushes location
        serializer = UserLocationHistorySerializer(data=request.data)
        if serializer.is_valid():
            # If we don't have legacy_location_id provided, default it to 0
            # because it is an integer field in DB
            serializer.save(legacy_location_id=request.data.get('legacy_location_id', 0))
            return Response({"Success": True, "Message": "Location saved"}, status=status.HTTP_201_CREATED)
        return Response({"Success": False, "Message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        # Fetch locations for a booking
        booking_id = request.query_params.get('booking_id')
        if not booking_id:
            return Response({"Success": False, "Message": "booking_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        booking = SlotBookingMaster.objects.filter(slot_booking_id=booking_id).first()
        is_completed = (booking is not None and str(booking.status or '').strip().lower() == 'completed')
        booking_status = booking.status if (booking and booking.status) else 'Pending'

        locations = UserLocationHistory.objects.filter(slot_booking_id=booking_id).order_by('timestamp')
        serializer = UserLocationHistorySerializer(locations, many=True)
        return Response({
            "Success": True, 
            "Markers": serializer.data,
            "is_completed": is_completed,
            "status": booking_status
        }, status=status.HTTP_200_OK)

@api_view(['POST'])
@throttle_classes([OTPRateThrottle])
@permission_classes([AllowAny])
def send_login_otp(request):
    mobile_or_username = request.data.get('mobile')
    if not mobile_or_username:
        return Response({"StatusCode": False, "Message": "Mobile number or username required"}, status=status.HTTP_400_BAD_REQUEST)
    
    from django.db import models
    user = User.objects.filter(models.Q(mobile_number=mobile_or_username) | models.Q(user_name=mobile_or_username)).first()
    
    if not user:
        return Response({"StatusCode": False, "Message": "User does not exist."}, status=status.HTTP_200_OK)
    
    actual_mobile = user.mobile_number
    if not actual_mobile:
        return Response({"StatusCode": False, "Message": "No mobile number attached to this user."}, status=status.HTTP_200_OK)

    otp_val = str(random.randint(100000, 999999))
    try:
        OtpMaster.objects.create(otp=otp_val, mobile=actual_mobile, otp_datetime=timezone.now())
        
        # Send SMS via Fast2SMS asynchronously
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": settings.FAST2SMS_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "route": "dlt",
            "sender_id": "XRAIHD",
            "message": "204048",
            "variables_values": otp_val,
            "numbers": actual_mobile
        }
        threading.Thread(target=send_sms_background, args=(url, headers, payload)).start()
        
        return Response({"StatusCode": True, "Message": "OTP has been sent to your registered mobile number.", "ActualMobile": actual_mobile}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"StatusCode": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_otp(request):
    mobile = request.data.get('mobile')
    otp = request.data.get('otp')

    if not mobile or not otp:
        return Response({"Success": False, "message": "Mobile number and OTP are required."}, status=status.HTTP_200_OK)

    latest_otp = OtpMaster.objects.filter(mobile=mobile).order_by('-otp_id').first()
    if latest_otp and latest_otp.otp == otp:
        user = User.objects.filter(mobile_number=mobile).first()
        if user:
            from django.core import signing
            token_payload = {
                "UserID": user.id,
                "UserType": user.user_type.user_type_name
            }
            auth_token = signing.dumps(token_payload)

            return Response({
                "Success": True, 
                "message": "User has been logged in successfully.",
                "Token": auth_token,
                "UserType": user.user_type.user_type_name,
                "UserID": user.id,
                "UserName": user.user_name,
                "FullName": user.full_name or user.user_name,
                "Age": user.age,
                "Gender": user.gender,
                "MobileNumber": user.mobile_number
            }, status=status.HTTP_200_OK)
        else:
            return Response({"Success": False, "message": "User not found."}, status=status.HTTP_200_OK)
    else:
        return Response({"Success": False, "message": "Invalid OTP."}, status=status.HTTP_200_OK)


class DPDPConsentLogViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = DPDPConsentLog.objects.all().order_by('-created_at')
    serializer_class = DPDPConsentLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['consent_id', 'patient_number', 'patient_id', 'full_name', 'email', 'shared_otp', 'status', 'notice_version']

    def get_queryset(self):
        queryset = DPDPConsentLog.objects.all().order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        patient_param = self.request.query_params.get('patient_number')
        if patient_param:
            queryset = queryset.filter(patient_number=patient_param)
        patient_id_param = self.request.query_params.get('patient_id')
        if patient_id_param:
            queryset = queryset.filter(patient_id=patient_id_param)
        consent_id_param = self.request.query_params.get('consent_id')
        if consent_id_param:
            queryset = queryset.filter(consent_id=consent_id_param)
        return queryset

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Allows SuperAdmin to record consent withdrawal or approve a patient's pending revocation request"""
        consent = self.get_object()
        reason = request.data.get('reason', 'SuperAdmin recorded consent withdrawal under DPDP Act Section 6(4)')
        withdrawn_by = request.data.get('withdrawn_by', 'SuperAdmin')
        consent.status = 'WITHDRAWN'
        meta = consent.metadata or {}

        # Mark request as approved if pending
        if 'withdrawal_request' in meta:
            meta['withdrawal_request']['status'] = 'APPROVED'
            meta['withdrawal_request']['approved_at'] = timezone.now().isoformat()
            meta['withdrawal_request']['approved_by'] = withdrawn_by

        meta['withdrawal'] = {
            'withdrawn_at': timezone.now().isoformat(),
            'reason': reason,
            'withdrawn_by': withdrawn_by,
            'approved_from_request': bool(meta.get('withdrawal_request'))
        }
        consent.metadata = meta
        consent.save()
        return Response({"Success": True, "Message": "Consent revoked and status updated to WITHDRAWN successfully.", "status": consent.status})

    @action(detail=True, methods=['post'])
    def reject_withdrawal(self, request, pk=None):
        """Allows SuperAdmin to reject or dismiss a pending consent revocation request"""
        consent = self.get_object()
        remarks = request.data.get('remarks', 'Revocation request rejected/dismissed by SuperAdmin')
        rejected_by = request.data.get('rejected_by', 'SuperAdmin')
        consent.status = 'ACTIVE'
        meta = consent.metadata or {}
        if 'withdrawal_request' in meta:
            meta['withdrawal_request']['status'] = 'REJECTED'
            meta['withdrawal_request']['rejected_at'] = timezone.now().isoformat()
            meta['withdrawal_request']['rejected_by'] = rejected_by
            meta['withdrawal_request']['remarks'] = remarks
        consent.metadata = meta
        consent.save()
        return Response({"Success": True, "Message": "Revocation request rejected. Consent remains ACTIVE.", "status": consent.status})

    @action(detail=False, methods=['get', 'post', 'patch'], url_path='my-consent')
    def my_consent(self, request):
        """Allows logged-in patient to view their DPDP consent record, update granular preferences, or submit a revocation request."""
        user_info = getattr(request, 'user_info', {})
        user_id = user_info.get('UserID') or request.query_params.get('user_id')
        user_name = user_info.get('UserName')

        user = None
        if user_id:
            user = User.objects.filter(id=user_id).first()
        elif user_name:
            user = User.objects.filter(user_name=user_name).first()

        consent = None
        if user:
            # 1. Search by patient_id
            consent = DPDPConsentLog.objects.filter(patient_id=user.id).order_by('-created_at').first()
            # 2. If not found, search by patient_number
            if not consent and user.mobile_number:
                consent = DPDPConsentLog.objects.filter(patient_number=user.mobile_number).order_by('-created_at').first()
            # 3. If not found, search by user ForeignKey
            if not consent:
                consent = DPDPConsentLog.objects.filter(user=user).order_by('-created_at').first()

        if request.method == 'GET':
            if not consent:
                return Response({
                    "Success": False,
                    "Message": "No DPDP consent record found for this patient account.",
                    "consent": None
                }, status=status.HTTP_200_OK)
            serializer = self.get_serializer(consent)
            return Response({
                "Success": True,
                "consent": serializer.data
            }, status=status.HTTP_200_OK)

        elif request.method in ['POST', 'PATCH']:
            action_type = request.data.get('action', 'update_preferences')

            if not consent:
                return Response({
                    "Success": False,
                    "Message": "No active consent record found to update."
                }, status=status.HTTP_404_NOT_FOUND)

            # Patient triggers a withdrawal request -> DOES NOT directly revoke. Sets PENDING_WITHDRAWAL for SuperAdmin approval!
            if action_type in ['withdraw', 'request_withdrawal']:
                reason = request.data.get('reason', 'Patient requested consent revocation via Privacy Hub')
                consent.status = 'PENDING_WITHDRAWAL'
                meta = consent.metadata or {}
                meta['withdrawal_request'] = {
                    'requested_at': timezone.now().isoformat(),
                    'reason': reason,
                    'patient_id': user.id if user else None,
                    'patient_name': user.full_name or user.user_name if user else None,
                    'patient_mobile': user.mobile_number if user else consent.patient_number,
                    'status': 'PENDING'
                }
                consent.metadata = meta
                consent.save()
                serializer = self.get_serializer(consent)
                return Response({
                    "Success": True,
                    "Message": "Your consent revocation request has been submitted. It is now pending review and approval by the SuperAdmin / Data Protection Officer.",
                    "consent": serializer.data
                }, status=status.HTTP_200_OK)

            elif action_type == 'cancel_withdrawal_request':
                if consent.status == 'PENDING_WITHDRAWAL':
                    consent.status = 'ACTIVE'
                    meta = consent.metadata or {}
                    if 'withdrawal_request' in meta:
                        meta['withdrawal_request']['status'] = 'CANCELLED'
                        meta['withdrawal_request']['cancelled_at'] = timezone.now().isoformat()
                    consent.metadata = meta
                    consent.save()
                serializer = self.get_serializer(consent)
                return Response({
                    "Success": True,
                    "Message": "Revocation request cancelled. Your consent remains Active.",
                    "consent": serializer.data
                }, status=status.HTTP_200_OK)

            elif action_type == 'update_preferences':
                optional_prefs = request.data.get('optional_preferences', {})
                purposes = consent.consented_purposes or {}
                opt_dict = purposes.get('optional', {})

                # Update matching clauses in the optional dictionary
                for clause_key in list(opt_dict.keys()):
                    key_lower = clause_key.lower()
                    if 'research' in key_lower and 'research' in optional_prefs:
                        opt_dict[clause_key] = bool(optional_prefs['research'])
                    elif ('offer' in key_lower or 'marketing' in key_lower) and 'marketing' in optional_prefs:
                        opt_dict[clause_key] = bool(optional_prefs['marketing'])
                    elif ('retention' in key_lower or 'period' in key_lower) and 'retention' in optional_prefs:
                        opt_dict[clause_key] = bool(optional_prefs['retention'])

                purposes['optional'] = opt_dict
                consent.consented_purposes = purposes

                # Append audit entry to metadata
                meta = consent.metadata or {}
                history = meta.get('preference_history', [])
                history.append({
                    'updated_at': timezone.now().isoformat(),
                    'updated_by': f"Patient ({user.full_name or user.user_name if user else 'Self'})",
                    'preferences': optional_prefs
                })
                meta['preference_history'] = history
                consent.metadata = meta
                consent.save()

                serializer = self.get_serializer(consent)
                return Response({
                    "Success": True,
                    "Message": "Privacy preferences updated successfully.",
                    "consent": serializer.data
                }, status=status.HTTP_200_OK)

            return Response({"Success": False, "Message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([AllowAny])
def consultant_exam_api(request):
    """
    Retrieves or saves the exam answers and progress for the authenticated Consultant.
    """
    user_info = getattr(request, 'user_info', {})
    data_dict = request.data if hasattr(request, 'data') and isinstance(request.data, dict) else {}
    user_id = user_info.get('UserID') or request.query_params.get('user_id') or data_dict.get('user_id')
    user_name = user_info.get('UserName') or request.query_params.get('username') or data_dict.get('username') or data_dict.get('user_name')

    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
    elif user_name:
        user = User.objects.filter(user_name=user_name).first()

    if not user:
        return Response({
            "Success": False,
            "Message": "Consultant user authentication required."
        }, status=status.HTTP_401_UNAUTHORIZED)

    exam_response = ConsultantExamResponse.objects.filter(user=user).order_by('-last_saved_at').first()
    if not exam_response:
        exam_response = ConsultantExamResponse.objects.create(
            user=user,
            exam_title='Primary Care Clinical Examination Module',
            answers={},
            current_view='intro',
            status='DRAFT',
            progress_stats={},
        )

    if request.method == 'GET':
        return Response({
            "Success": True,
            "exam_id": exam_response.id,
            "consultant": {
                "id": user.id,
                "user_name": user.user_name,
                "full_name": user.full_name or user.user_name,
                "email": user.email,
                "mobile": user.mobile_number,
            },
            "answers": exam_response.answers or {},
            "current_view": exam_response.current_view or 'intro',
            "status": exam_response.status,
            "progress_stats": exam_response.progress_stats or {},
            "compiled_summary": exam_response.compiled_summary,
            "last_saved_at": exam_response.last_saved_at.isoformat() if exam_response.last_saved_at else None,
            "submitted_at": exam_response.submitted_at.isoformat() if exam_response.submitted_at else None,
        }, status=status.HTTP_200_OK)

    elif request.method in ['POST', 'PATCH']:
        answers_data = request.data.get('answers')
        current_view = request.data.get('current_view')
        progress_stats = request.data.get('progress_stats')
        compiled_summary = request.data.get('compiled_summary')
        action = request.data.get('action')  # 'save' or 'submit'

        if answers_data is not None:
            exam_response.answers = answers_data
        if current_view is not None:
            exam_response.current_view = str(current_view)
        if progress_stats is not None:
            exam_response.progress_stats = progress_stats
        if compiled_summary is not None:
            exam_response.compiled_summary = compiled_summary

        if action == 'submit':
            exam_response.status = 'SUBMITTED'
            exam_response.submitted_at = timezone.now()

        exam_response.save()

        return Response({
            "Success": True,
            "Message": "Exam packet submitted successfully." if action == 'submit' else "Exam answers saved successfully.",
            "exam_id": exam_response.id,
            "status": exam_response.status,
            "last_saved_at": exam_response.last_saved_at.isoformat() if exam_response.last_saved_at else None,
            "submitted_at": exam_response.submitted_at.isoformat() if exam_response.submitted_at else None,
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def consultant_exam_submit(request):
    """
    Explicit submit endpoint for finalizing consultant exam submission.
    """
    user_info = getattr(request, 'user_info', {})
    data_dict = request.data if hasattr(request, 'data') and isinstance(request.data, dict) else {}
    user_id = user_info.get('UserID') or request.query_params.get('user_id') or data_dict.get('user_id')
    user_name = user_info.get('UserName') or request.query_params.get('username') or data_dict.get('username') or data_dict.get('user_name')

    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()
    elif user_name:
        user = User.objects.filter(user_name=user_name).first()

    if not user:
        return Response({
            "Success": False,
            "Message": "Consultant user authentication required."
        }, status=status.HTTP_401_UNAUTHORIZED)

    exam_response = ConsultantExamResponse.objects.filter(user=user).order_by('-last_saved_at').first()
    if not exam_response:
        exam_response = ConsultantExamResponse.objects.create(user=user)

    answers_data = request.data.get('answers')
    if answers_data is not None:
        exam_response.answers = answers_data
    compiled_summary = request.data.get('compiled_summary')
    if compiled_summary is not None:
        exam_response.compiled_summary = compiled_summary
    progress_stats = request.data.get('progress_stats')
    if progress_stats is not None:
        exam_response.progress_stats = progress_stats

    exam_response.status = 'SUBMITTED'
    exam_response.submitted_at = timezone.now()
    exam_response.save()

    return Response({
        "Success": True,
        "Message": "Exam packet submitted successfully.",
        "exam_id": exam_response.id,
        "status": exam_response.status,
        "submitted_at": exam_response.submitted_at.isoformat(),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def consultant_submissions_list(request):
    """
    List all consultant examination submissions with filtering, search, and activity metrics.
    """
    qs = ConsultantExamResponse.objects.select_related('user', 'evaluated_by').all()

    # Search filter
    search_q = request.query_params.get('search', '').strip()
    if search_q:
        qs = qs.filter(
            Q(user__user_name__icontains=search_q) |
            Q(user__full_name__icontains=search_q) |
            Q(user__mobile_number__icontains=search_q) |
            Q(admin_notes__icontains=search_q)
        )

    # Status filter
    status_filter = request.query_params.get('status', '').strip().upper()
    if status_filter and status_filter != 'ALL':
        qs = qs.filter(status=status_filter)

    # Ordering
    order_by = request.query_params.get('ordering', '-last_saved_at')
    valid_orders = ['-last_saved_at', 'last_saved_at', '-submitted_at', 'submitted_at', '-started_at', 'started_at', 'status', '-status']
    if order_by in valid_orders:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by('-last_saved_at')

    # Metrics computation across all consultant exams
    all_responses = ConsultantExamResponse.objects.all()
    total_consultants = User.objects.filter(user_type__user_type_name='Consultant').count()
    total_submissions = all_responses.count()
    submitted_count = all_responses.filter(status='SUBMITTED').count()
    draft_count = all_responses.filter(status='DRAFT').count()
    evaluated_count = all_responses.filter(status__in=['EVALUATED', 'APPROVED']).count()

    total_coverage = 0
    covered_items = 0
    for r in all_responses:
        stats = r.progress_stats or {}
        pct = stats.get('percent', 0)
        total_coverage += pct
        covered_items += 1
    avg_coverage = round(total_coverage / covered_items, 1) if covered_items > 0 else 0

    results = []
    for s in qs:
        stats = s.progress_stats or {}
        results.append({
            "id": s.id,
            "user_id": s.user.id if s.user else None,
            "username": s.user.user_name if s.user else 'Unknown',
            "full_name": s.user.full_name or (s.user.user_name if s.user else ''),
            "mobile_number": s.user.mobile_number if s.user else '',
            "status": s.status,
            "current_view": s.current_view,
            "progress_stats": stats,
            "completed_cases": stats.get('completed_cases', 0),
            "total_cases": stats.get('total_cases', 13),
            "percent": stats.get('percent', 0),
            "answered_count": len(s.answers.keys()) if isinstance(s.answers, dict) else 0,
            "admin_notes": s.admin_notes or '',
            "evaluated_at": s.evaluated_at.isoformat() if s.evaluated_at else None,
            "evaluated_by_name": s.evaluated_by.full_name or s.evaluated_by.user_name if s.evaluated_by else None,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "last_saved_at": s.last_saved_at.isoformat() if s.last_saved_at else None,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        })

    return Response({
        "Success": True,
        "Metrics": {
            "total_consultants": total_consultants,
            "total_submissions": total_submissions,
            "submitted_count": submitted_count,
            "draft_count": draft_count,
            "evaluated_count": evaluated_count,
            "avg_coverage": avg_coverage,
        },
        "Total": len(results),
        "Submissions": results
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])
def consultant_submission_detail(request, id):
    """
    Retrieve full details, update evaluation status / notes, or delete a consultant submission.
    """
    submission = ConsultantExamResponse.objects.select_related('user', 'evaluated_by').filter(id=id).first()
    if not submission:
        return Response({"Success": False, "Message": "Consultant submission not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            "Success": True,
            "submission": {
                "id": submission.id,
                "user_id": submission.user.id if submission.user else None,
                "username": submission.user.user_name if submission.user else 'Unknown',
                "full_name": submission.user.full_name or (submission.user.user_name if submission.user else ''),
                "mobile_number": submission.user.mobile_number if submission.user else '',
                "email": submission.user.email if submission.user else '',
                "exam_title": submission.exam_title,
                "status": submission.status,
                "current_view": submission.current_view,
                "progress_stats": submission.progress_stats or {},
                "answers": submission.answers or {},
                "compiled_summary": submission.compiled_summary or '',
                "admin_notes": submission.admin_notes or '',
                "evaluated_at": submission.evaluated_at.isoformat() if submission.evaluated_at else None,
                "evaluated_by_name": submission.evaluated_by.full_name or submission.evaluated_by.user_name if submission.evaluated_by else None,
                "started_at": submission.started_at.isoformat() if submission.started_at else None,
                "last_saved_at": submission.last_saved_at.isoformat() if submission.last_saved_at else None,
                "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            }
        }, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes')

        if new_status and new_status in dict(ConsultantExamResponse.STATUS_CHOICES):
            submission.status = new_status
            if new_status in ['EVALUATED', 'APPROVED']:
                submission.evaluated_at = timezone.now()
                user_info = getattr(request, 'user_info', {})
                eval_user_id = user_info.get('UserID')
                if eval_user_id:
                    submission.evaluated_by = User.objects.filter(id=eval_user_id).first()
            elif new_status == 'DRAFT':
                submission.submitted_at = None

        if admin_notes is not None:
            submission.admin_notes = admin_notes

        submission.save()

        return Response({
            "Success": True,
            "Message": "Submission updated successfully.",
            "status": submission.status,
            "admin_notes": submission.admin_notes,
            "evaluated_at": submission.evaluated_at.isoformat() if submission.evaluated_at else None,
        }, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        submission.delete()
        return Response({"Success": True, "Message": "Consultant submission deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def consultant_submission_download(request, id):
    """
    Download a single consultant submission as a formatted text file.
    """
    submission = ConsultantExamResponse.objects.select_related('user').filter(id=id).first()
    if not submission:
        return Response({"Success": False, "Message": "Consultant submission not found."}, status=status.HTTP_404_NOT_FOUND)

    doc_name = (submission.user.full_name or submission.user.user_name or "Consultant").replace(' ', '_')
    summary_text = submission.compiled_summary
    if not summary_text:
        summary_text = f"Consultant: Dr. {doc_name}\nStatus: {submission.status}\nLast Saved: {submission.last_saved_at}\n\n(No compiled summary text available.)"

    response = HttpResponse(summary_text, content_type='text/plain; charset=utf-8')
    filename = f"Consultant_Evaluation_{doc_name}_{submission.last_saved_at.strftime('%Y%m%d') if submission.last_saved_at else 'report'}.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def consultant_submissions_export_csv(request):
    """
    Export all consultant submissions to CSV format for download.
    """
    submissions = ConsultantExamResponse.objects.select_related('user', 'evaluated_by').all().order_by('-last_saved_at')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="Consultant_Evaluations_Summary_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Submission ID",
        "Username",
        "Doctor Full Name",
        "Mobile Number",
        "Status",
        "Completed Cases",
        "Total Cases",
        "Coverage (%)",
        "Current Tab",
        "Started At",
        "Last Saved At",
        "Submitted At",
        "Evaluated At",
        "Evaluated By",
        "Admin Notes"
    ])

    for s in submissions:
        stats = s.progress_stats or {}
        writer.writerow([
            s.id,
            s.user.user_name if s.user else '',
            s.user.full_name if s.user else '',
            s.user.mobile_number if s.user else '',
            s.status,
            stats.get('completed_cases', 0),
            stats.get('total_cases', 13),
            f"{stats.get('percent', 0)}%",
            s.current_view,
            s.started_at.strftime('%Y-%m-%d %H:%M:%S') if s.started_at else '',
            s.last_saved_at.strftime('%Y-%m-%d %H:%M:%S') if s.last_saved_at else '',
            s.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if s.submitted_at else '',
            s.evaluated_at.strftime('%Y-%m-%d %H:%M:%S') if s.evaluated_at else '',
            s.evaluated_by.full_name or s.evaluated_by.user_name if s.evaluated_by else '',
            s.admin_notes or ''
        ])

    return response






@api_view(['POST'])
@permission_classes([AllowAny])
def submit_technician_onboarding(request):
    try:
        data = request.data.copy()
        
        full_name = data.get('full_name', '').strip()
        mobile_number = data.get('mobile_number', '').strip()
        address = data.get('address', '').strip()
        
        if not full_name or not mobile_number or not address:
            return Response({
                'Success': False,
                'Message': 'Full Name, Mobile Number, and Address are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        import json
        skills_raw = data.get('skills')
        if skills_raw:
            if isinstance(skills_raw, str):
                try:
                    json.loads(skills_raw)
                except Exception:
                    items = [s.strip() for s in skills_raw.split(',') if s.strip()]
                    data['skills'] = json.dumps(items)
            elif isinstance(skills_raw, list):
                data['skills'] = json.dumps(skills_raw)

        serializer = TechnicianOnboardingSerializer(data=data)
        if serializer.is_valid():
            onboarding = serializer.save()
            return Response({
                'Success': True,
                'Message': 'Application submitted successfully! Our team will review your application shortly.',
                'id': onboarding.id,
                'status': onboarding.status
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'Success': False,
                'Message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'Success': False,
            'Message': f"Submission error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_technician_confirmation_email(app, agreed_rates=None, custom_message=None):
    if not app.email:
        raise ValueError("Technician does not have an email address provided.")
    
    import json
    rates_raw = agreed_rates or app.agreed_rates
    rates_list = []
    rates_is_tabular = False

    if rates_raw:
        if isinstance(rates_raw, list):
            rates_list = rates_raw
            rates_is_tabular = True
        elif isinstance(rates_raw, str):
            try:
                parsed = json.loads(rates_raw)
                if isinstance(parsed, list):
                    rates_list = parsed
                    rates_is_tabular = True
            except Exception:
                pass

    if rates_is_tabular and rates_list:
        rates_rows_html = "".join([
            f"""
            <tr style="border-bottom: 1px solid #e2e8f0; font-size: 13px;">
              <td style="padding: 10px 12px; font-weight: 600; color: #0f172a;">{r.get('service', 'Service')}</td>
              <td style="padding: 10px 12px; font-weight: 800; color: #0f766e;">₹{r.get('rate', '0')}</td>
              <td style="padding: 10px 12px; color: #475569; font-size: 12px;">{r.get('unit', 'Per Case')}</td>
              <td style="padding: 10px 12px; color: #64748b; font-size: 12px;">{r.get('notes', '')}</td>
            </tr>
            """
            for r in rates_list
        ])
        rates_html_block = f"""
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #ccfbf1;">
          <thead>
            <tr style="background: #0f766e; color: #ffffff; text-align: left; font-size: 11px; text-transform: uppercase;">
              <th style="padding: 9px 12px;">Service / Modality</th>
              <th style="padding: 9px 12px;">Agreed Rate</th>
              <th style="padding: 9px 12px;">Billing Unit</th>
              <th style="padding: 9px 12px;">Remarks</th>
            </tr>
          </thead>
          <tbody>
            {rates_rows_html}
          </tbody>
        </table>
        """
        rates_plain_text = "\n".join([
            f"  - {r.get('service')}: ₹{r.get('rate')} ({r.get('unit')}) {('(' + r.get('notes') + ')') if r.get('notes') else ''}"
            for r in rates_list
        ])
    else:
        rates_display_text = str(rates_raw or "Standard rates as discussed with operations team")
        rates_html_block = f'<div style="font-size: 14px; font-weight: 700; color: #134e4a; white-space: pre-wrap;">{rates_display_text}</div>'
        rates_plain_text = rates_display_text

    skills_display = ", ".join(app.skills) if isinstance(app.skills, list) else str(app.skills or "Diagnostic Procedures")
    
    subject = "Welcome to XRAi Digital Field Network - Application Approved!"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@xraidigital.com')
    to_email = [app.email]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333333; margin: 0; padding: 0; background-color: #f4f6f9; }}
        .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .header {{ background: linear-gradient(135deg, #172554, #008ba3); color: #ffffff; padding: 30px 25px; text-align: center; }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }}
        .header p {{ margin: 0; font-size: 14px; color: #e0f2fe; }}
        .body-content {{ padding: 30px 25px; }}
        .badge-success {{ display: inline-block; background-color: #dcfce7; color: #166534; font-weight: bold; font-size: 12px; padding: 4px 12px; border-radius: 50px; text-transform: uppercase; margin-bottom: 15px; }}
        .rates-card {{ background-color: #f0fdfa; border: 2px dashed #00acc1; border-radius: 10px; padding: 18px; margin: 20px 0; }}
        .rates-card h3 {{ margin: 0 0 10px 0; color: #0f766e; font-size: 16px; font-weight: bold; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .details-table td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }}
        .details-table td.label {{ color: #64748b; font-weight: 600; width: 38%; }}
        .details-table td.value {{ color: #0f172a; font-weight: 600; }}
        .steps {{ background: #f8fafc; border-radius: 10px; padding: 18px; margin: 20px 0; }}
        .steps h4 {{ margin: 0 0 10px 0; color: #1e293b; font-size: 14px; font-weight: bold; }}
        .steps ol {{ margin: 0; padding-left: 20px; font-size: 13px; color: #475569; }}
        .steps li {{ margin-bottom: 8px; }}
        .footer {{ background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>XRAi Digital Field Network</h1>
          <p>Care at Home Diagnostic Services</p>
        </div>
        <div class="body-content">
          <span class="badge-success">&#10003; Application Approved</span>
          <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 20px;">Dear {app.full_name},</h2>
          <p style="font-size: 14px; color: #334155; margin-bottom: 16px;">
            We are pleased to inform you that your onboarding application to join <strong>XRAi Digital</strong> as a Field Diagnostic Technician has been <strong>approved</strong>!
          </p>
          
          {f'<div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #0369a1;">{custom_message}</div>' if custom_message else ''}

          <div class="rates-card">
            <h3>Agreed Technician Payout Rates:</h3>
            {rates_html_block}
          </div>

          <table class="details-table">
            <tr>
              <td class="label">Approved Modalities:</td>
              <td class="value">{skills_display}</td>
            </tr>
            <tr>
              <td class="label">Operating Location:</td>
              <td class="value">{app.work_location}</td>
            </tr>
            <tr>
              <td class="label">Contact Mobile:</td>
              <td class="value">{app.mobile_number}</td>
            </tr>
            <tr>
              <td class="label">Registered Bank:</td>
              <td class="value">{app.bank_name or 'On file'}</td>
            </tr>
          </table>

          <div class="steps">
            <h4>Next Steps for Field Deployment:</h4>
            <ol>
              <li>Our Field Operations Coordinator will connect with you on <strong>{app.mobile_number}</strong> to coordinate kit verification and route assignments.</li>
              <li>You will receive your <strong>Technician Mobile App credentials</strong> to start receiving home-visit diagnostic bookings.</li>
              <li>All completed cases will be logged on your app and payouts will be credited per the agreed rates above.</li>
            </ol>
          </div>

          <p style="font-size: 13px; color: #475569; margin-top: 24px;">
            If you have any questions or require support, please contact operations at <a href="mailto:info@xraidigital.com" style="color: #00acc1; font-weight: 600;">info@xraidigital.com</a> or Toll-Free <strong>1800 270 2900</strong>.
          </p>
        </div>
        <div class="footer">
          <p style="margin: 0 0 4px 0;"><strong>XRAi Digital</strong> &bull; A Unit of U4RAD Technologies Pvt Ltd</p>
          <p style="margin: 0;">CIN: U86100HR2024PTC120732 | Gurgaon & Kolkata, India</p>
        </div>
      </div>
    </body>
    </html>
    """

    plain_message = f"""Dear {app.full_name},

Congratulations! Your onboarding application to join XRAi Digital as a Field Diagnostic Technician has been APPROVED.

AGREED PAYOUT RATES:
{rates_plain_text}

Approved Modalities: {skills_display}
Operating Location: {app.work_location}
Contact Mobile: {app.mobile_number}
Registered Bank: {app.bank_name or 'On file'}

NEXT STEPS:
1. Our Field Operations Coordinator will connect with you on {app.mobile_number} to coordinate kit verification and route assignments.
2. You will receive your Technician Mobile App credentials to start receiving home-visit diagnostic bookings.
3. All completed cases will be logged on your app and payouts will be credited per the agreed rates above.

Best regards,
XRAi Digital Field Operations Team
A Unit of U4RAD Technologies Pvt Ltd
Email: info@xraidigital.com | Toll-Free: 1800 270 2900
"""

    msg = EmailMultiAlternatives(subject, plain_message, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


@api_view(['GET', 'PATCH', 'POST'])
def admin_technician_onboardings(request):
    if request.method == 'GET':
        status_filter = request.query_params.get('status')
        search_query = request.query_params.get('search')
        
        qs = TechnicianOnboarding.objects.all().order_by('-created_at')
        if status_filter and status_filter.upper() != 'ALL':
            qs = qs.filter(status=status_filter.upper())
        if search_query:
            qs = qs.filter(
                Q(full_name__icontains=search_query) |
                Q(mobile_number__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(work_location__icontains=search_query) |
                Q(education_qualification__icontains=search_query)
            )
            
        stats = {
            'total_applications': TechnicianOnboarding.objects.count(),
            'pending_review': TechnicianOnboarding.objects.filter(status='PENDING').count(),
            'approved_working': TechnicianOnboarding.objects.filter(status='APPROVED').count(),
            'rejected': TechnicianOnboarding.objects.filter(status='REJECTED').count(),
        }
        
        serializer = TechnicianOnboardingSerializer(qs, many=True)
        return Response({
            'Success': True,
            'stats': stats,
            'applications': serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method in ('PATCH', 'POST'):
        app_id = request.data.get('id')
        new_status = request.data.get('status')
        agreed_rates = request.data.get('agreed_rates')
        admin_notes = request.data.get('admin_notes')
        send_email = request.data.get('send_email', False)
        custom_message = request.data.get('custom_message')
        
        if not app_id:
            return Response({'Success': False, 'Message': 'Application id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            app = TechnicianOnboarding.objects.get(id=app_id)
            if new_status:
                app.status = new_status.upper()
            if agreed_rates is not None:
                if isinstance(agreed_rates, (list, dict)):
                    import json
                    app.agreed_rates = json.dumps(agreed_rates)
                else:
                    app.agreed_rates = str(agreed_rates).strip()
            if admin_notes is not None:
                app.admin_notes = admin_notes.strip()
            app.reviewed_at = timezone.now()

            email_sent = False
            email_error = None
            if send_email:
                if not app.email:
                    email_error = "Technician has no email address on file."
                else:
                    try:
                        send_technician_confirmation_email(app, agreed_rates=app.agreed_rates, custom_message=custom_message)
                        email_sent = True
                        app.email_sent = True
                        app.email_sent_at = timezone.now()
                    except Exception as em_err:
                        email_error = str(em_err)
                        print(f"Error sending technician approval email: {em_err}")

            app.save()

            msg = "Application updated successfully."
            if new_status:
                msg = f"Application marked as {new_status}."
            if email_sent:
                msg += f" Confirmation email sent to {app.email}."
            elif email_error:
                msg += f" (Note: Email could not be delivered: {email_error})"

            return Response({
                'Success': True,
                'Message': msg,
                'email_sent': email_sent,
                'email_error': email_error,
                'application': TechnicianOnboardingSerializer(app).data
            }, status=status.HTTP_200_OK)
        except TechnicianOnboarding.DoesNotExist:
            return Response({'Success': False, 'Message': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
