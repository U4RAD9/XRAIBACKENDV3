from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import base64
import os
import datetime
import razorpay # type: ignore
from django.conf import settings

from .models import SlotBookingMaster, SlotBookingDetails
from .serializers import SlotBookingMasterSerializer, SlotBookingDetailsSerializer

class SlotBookingMasterViewSet(viewsets.ModelViewSet):
    queryset = SlotBookingMaster.objects.all()
    serializer_class = SlotBookingMasterSerializer

class SlotBookingDetailsViewSet(viewsets.ModelViewSet):
    queryset = SlotBookingDetails.objects.all()
    serializer_class = SlotBookingDetailsSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def get_price(request):
    location_id = request.query_params.get('location_id')
    service_id = request.query_params.get('service_id')
    group_id = request.query_params.get('group_id')
    visit_type_id = request.query_params.get('visit_type_id')

    price = 1500 # Default fallback
    if group_id == '1':
        price = 1000
    elif group_id == '2':
        price = 2500

    return Response({"Price": price}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def save_booking(request):
    try:
        data = request.data
        user_id = data.get('user_id')
        location_id = data.get('location_id')
        patient_id = data.get('patient_id')
        date = data.get('date')
        slot_id = data.get('slot_id')
        address = data.get('address')
        amount = data.get('amount')
        
        payment_method = data.get('payment_method')
        payment_status = data.get('payment_status', 'Pending')
        services = data.get('services', [])
        consent_given = data.get('consent_given', False)
        
        # Calculate amount if not provided
        if not amount and services:
            amount = sum([float(s.get('price') or 0) for s in services])

        from users.models import User
        from patients.models import Patient
        from locations.models import Location
        from slots.models import SlotMaster
        from services.models import Service

        user = User.objects.get(id=user_id) if user_id else None
        patient = Patient.objects.get(patient_id=patient_id) if patient_id else None
        location = Location.objects.get(location_id=location_id) if location_id else None
        slot = SlotMaster.objects.get(slot_id=slot_id) if slot_id else None

        booking = SlotBookingMaster.objects.create(
            user=user,
            patient=patient,
            location=location,
            slot=slot,
            address=address,
            gross_amount=amount,
            net_amount=amount,
            status='Pending',
            payment_status=payment_status,
            payment_method=payment_method,
            consent_given=consent_given
        )
        
        if date:
            # Simple parse or assign date directly if model takes string, but better to set datetime
            # We'll just assign it to slot_booking_datetime for now
            booking.slot_booking_datetime = date
            booking.save()

        for svc_data in services:
            service_id = svc_data.get('service_id')
            price = svc_data.get('price') or 0
            service_obj = Service.objects.get(service_id=service_id) if service_id else None
            if service_obj:
                SlotBookingDetails.objects.create(
                    slot_booking=booking,
                    service=service_obj,
                    price=price
                )

        return Response({"Success": True, "Message": "Booking saved successfully", "BookingID": booking.slot_booking_id}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_bookings(request):
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"Success": False, "Message": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    bookings = SlotBookingMaster.objects.filter(user_id=user_id).order_by('-created_date')
    data = []
    for b in bookings:
        data.append({
            "BookingID": b.slot_booking_id,
            "Date": b.slot_booking_datetime.strftime('%Y-%m-%d') if b.slot_booking_datetime else b.created_date.strftime('%Y-%m-%d'),
            "Amount": str(b.net_amount) if b.net_amount else "0",
            "Status": b.status,
            "ServiceGroupName": b.service_group.service_group_name if b.service_group else "General Service"
        })
    return Response({"Success": True, "Bookings": data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_last_booking(request):
    patient_id = request.query_params.get('patient_id')
    if not patient_id:
        return Response({"Success": False, "Message": "patient_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    last_booking = SlotBookingMaster.objects.filter(patient_id=patient_id).order_by('-created_date').first()
    if not last_booking:
        return Response({"Success": False, "Message": "No booking found"}, status=status.HTTP_404_NOT_FOUND)
        
    services = []
    details = SlotBookingDetails.objects.filter(slot_booking=last_booking)
    for detail in details:
        services.append({
            "service_id": detail.service.service_id if detail.service else None,
            "service_group_id": detail.service.service_group.service_group_id if detail.service and detail.service.service_group else None,
            "price": str(detail.price) if detail.price else "0",
            "service_name": detail.service.service_name if detail.service else None,
            "service_group_name": detail.service.service_group.service_group_name if detail.service and detail.service.service_group else None
        })
        
    data = {
        "location_id": last_booking.location.location_id if last_booking.location else None,
        "slot_id": last_booking.slot.slot_id if last_booking.slot else None,
        "date": last_booking.slot_booking_datetime.strftime('%Y-%m-%d') if last_booking.slot_booking_datetime else None,
        "payment_method": last_booking.payment_method,
        "address": last_booking.address,
        "services": services
    }
    
    return Response({"Success": True, "Booking": data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_bookings(request):
    date = request.query_params.get('date')
    status_filter = request.query_params.get('status')
    
    query = SlotBookingMaster.objects.all().order_by('-created_date')
    if date:
        query = query.filter(created_date__date=date)
    if status_filter and status_filter != 'All':
        query = query.filter(status=status_filter)
        
    data = []
    for b in query:
        data.append({
            "id": b.slot_booking_id,
            "patientId": b.patient.patient_id if b.patient else "N/A",
            "phoneNo": b.patient.alternate_mobile_number if b.patient and b.patient.alternate_mobile_number else (b.user.mobile_number if b.user and b.user.mobile_number else (b.phone_number or "N/A")),
            "patientName": b.patient.patient_name if b.patient and b.patient.patient_name else (b.patient_name or "N/A"),
            "refNo": f"REF-{b.slot_booking_id}",
            "bookingDate": b.slot_booking_datetime.strftime('%Y-%m-%d') if b.slot_booking_datetime else (b.created_date.strftime('%Y-%m-%d') if b.created_date else "N/A"),
            "slot": b.slot.slot_name if b.slot and b.slot.slot_name else "N/A",
            "paymentMethod": b.payment_method or "N/A",
            "paymentStatus": b.payment_status or "N/A",
            "technician": b.service_provider.full_name if b.service_provider and b.service_provider.full_name else (b.service_provider.user_name if b.service_provider else "N/A"),
            "remarks": "N/A",
            "isActive": b.is_active if b.is_active is not None else True,
            # Legacy fields for dashboard compatibility
            "mobile": b.user.mobile_number if b.user else b.phone_number,
            "service": b.service_group.service_group_name if b.service_group else "General",
            "date": b.slot_booking_datetime.strftime('%Y-%m-%d') if b.slot_booking_datetime else (b.created_date.strftime('%Y-%m-%d') if b.created_date else ""),
            "time": b.slot.slot_name if b.slot else "N/A",
            "status": b.status,
            "amount": float(b.net_amount) if b.net_amount else 0.0,
            "address": b.booking_address or b.address
        })
        
    return Response({"Success": True, "result": data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_booking_details(request, id):
    try:
        b = SlotBookingMaster.objects.get(slot_booking_id=id)
        
        services = []
        details = SlotBookingDetails.objects.filter(slot_booking=b)
        for detail in details:
            services.append({
                "id": detail.slot_booking_det_id,
                "service_id": detail.service.service_id if detail.service else None,
                "service": detail.service.service_group.service_group_name if detail.service and detail.service.service_group else "N/A",
                "bodyPart": detail.service.service_name if detail.service else "N/A",
                "price": str(detail.price) if detail.price else "0",
                "netPayable": str(detail.price) if detail.price else "0",
                "serviceFile": detail.service_filename if hasattr(detail, 'service_filename') else None,
                "reportFile": detail.report_filename if hasattr(detail, 'report_filename') else None
            })
            
        data = {
            "id": b.slot_booking_id,
            "location_name": b.location.location_name if b.location else "N/A",
            "slot_name": b.slot.slot_name if b.slot else "N/A",
            "visit_type": "Home",
            "visit_date": b.slot_booking_datetime.strftime('%Y-%m-%d') if b.slot_booking_datetime else (b.created_date.strftime('%Y-%m-%d') if b.created_date else "N/A"),
            "payment_mode": b.payment_method or "N/A",
            "technician_id": b.service_provider.id if b.service_provider else "",
            "created_on": b.created_date.strftime('%d-%m-%Y %H:%M:%S') if b.created_date else "N/A",
            "patient": {
                "phoneNo": b.patient.alternate_mobile_number if b.patient and b.patient.alternate_mobile_number else (b.user.mobile_number if b.user and b.user.mobile_number else (b.phone_number or "N/A")),
                "patientName": b.patient.patient_name if b.patient and b.patient.patient_name else (b.patient_name or "N/A"),
                "weight": b.patient.weight if b.patient and b.patient.weight is not None else "0",
                "address": b.booking_address or b.address or (b.patient.address if b.patient else "N/A"),
                "email": b.patient.email if b.patient and b.patient.email else (b.user.email if b.user else "N/A"),
                "age": b.patient.age if b.patient and b.patient.age is not None else "N/A",
                "gender": b.patient.gender if b.patient and b.patient.gender else "N/A",
                "pin": b.patient.pin if b.patient and b.patient.pin else "N/A",
                "alternateNo": b.patient.alternate_mobile_number if b.patient and b.patient.alternate_mobile_number else "N/A"
            },
            "prescriptionFile": b.prescription_filename if hasattr(b, 'prescription_filename') else None,
            "services": services
        }
        return Response({"Success": True, "Booking": data}, status=status.HTTP_200_OK)
    except SlotBookingMaster.DoesNotExist:
        return Response({"Success": False, "Message": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_booking_file(request, id):
    try:
        detail = SlotBookingDetails.objects.get(slot_booking_det_id=id)
        file_obj = request.FILES.get('file')
        file_type = request.data.get('type') # 'Service' or 'Report'
        
        if not file_obj or not file_type:
            return Response({"Success": False, "Message": "File or type missing"}, status=status.HTTP_400_BAD_REQUEST)
            
        fs = FileSystemStorage()
        filename = fs.save(file_obj.name, file_obj)
        extension = os.path.splitext(filename)[1]
        
        if file_type == 'Service':
            detail.service_filename = filename
            detail.service_extension = extension
        elif file_type == 'Report':
            detail.report_filename = filename
            detail.report_extension = extension
            
        detail.save()
        
        return Response({"Success": True, "Message": "File uploaded successfully", "filename": filename}, status=status.HTTP_200_OK)
    except SlotBookingDetails.DoesNotExist:
        return Response({"Success": False, "Message": "Service detail not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    amount = request.data.get('amount')
    currency = 'INR'
    
    try:
        # Mocking razorpay response
        order = {
            "id": "order_mock12345",
            "amount": int(amount) * 100 if amount else 0,
            "currency": currency
        }
        return Response({"order_id": order['id'], "amount": order['amount']}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request):
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_signature = request.data.get('razorpay_signature')
    return Response({"status": "success", "PaymentID": razorpay_payment_id}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    try:
        from_date = request.query_params.get('FromDate')
        to_date = request.query_params.get('ToDate')
        
        query = SlotBookingMaster.objects.all()
        
        if from_date and to_date:
            query = query.filter(slot_booking_datetime__date__gte=from_date, slot_booking_datetime__date__lte=to_date)
            
        pending_bookings = query.filter(status='Pending').count()
        confirmed_bookings = query.filter(status='Booked').count()
        in_progress_bookings = query.filter(status='In Progress').count()
        completed_bookings = query.filter(status='Completed').count()
        
        result = {
            "PendingBookings": pending_bookings,
            "ConfirmedBookings": confirmed_bookings,
            "BookingInProgress": in_progress_bookings,
            "BookingPerformed": completed_bookings,
            "ReportFilesUploaded": 0,
            "ServiceFilesUploaded": 0
        }
        return Response({"Success": True, "result": result}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)
@api_view(['POST'])
@permission_classes([AllowAny])
def upload_prescription_file(request, id):
    try:
        from django.core.files.storage import FileSystemStorage
        import os
        booking = SlotBookingMaster.objects.get(slot_booking_id=id)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'Success': False, 'Message': 'File missing'}, status=status.HTTP_400_BAD_REQUEST)
        fs = FileSystemStorage()
        filename = fs.save(file_obj.name, file_obj)
        extension = os.path.splitext(filename)[1]
        
        booking.prescription_filename = filename
        booking.save()
        return Response({'Success': True, 'Message': 'Prescription uploaded successfully', 'filename': filename}, status=status.HTTP_200_OK)
    except SlotBookingMaster.DoesNotExist:
        return Response({'Success': False, 'Message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'Success': False, 'Message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'PATCH'])
@permission_classes([AllowAny])
def update_booking_status(request, id):
    try:
        booking = SlotBookingMaster.objects.get(slot_booking_id=id)
        booking.status = 'Completed'
        booking.save()
        return Response({'Success': True, 'Message': 'Status updated to Completed'}, status=status.HTTP_200_OK)
    except SlotBookingMaster.DoesNotExist:
        return Response({'Success': False, 'Message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'Success': False, 'Message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST', 'PATCH'])
@permission_classes([AllowAny])
def update_payment_status(request, id):
    try:
        booking = SlotBookingMaster.objects.get(slot_booking_id=id)
        booking.payment_status = 'Paid'
        booking.save()
        return Response({'Success': True, 'Message': 'Payment status updated to Paid'}, status=status.HTTP_200_OK)
    except SlotBookingMaster.DoesNotExist:
        return Response({'Success': False, 'Message': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'Success': False, 'Message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_technician_bookings(request):
    technician_id = request.query_params.get('technician_id')
    if not technician_id:
        return Response({"Success": False, "Message": "technician_id is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    query = SlotBookingMaster.objects.filter(service_provider_id=technician_id).order_by('-created_date')
    
    pending_bookings = query.exclude(status='Completed').count()
    completed_bookings = query.filter(status='Completed').count()
    
    data = []
    for b in query:
        details = SlotBookingDetails.objects.filter(slot_booking=b)
        files_count = 0
        for d in details:
            if d.service_filename:
                files_count += 1
            if d.report_filename:
                files_count += 1
                
        data.append({
            "id": b.slot_booking_id,
            "patientId": b.patient.patient_id if b.patient else "N/A",
            "phoneNo": b.patient.alternate_mobile_number if b.patient and b.patient.alternate_mobile_number else (b.user.mobile_number if b.user and b.user.mobile_number else (b.phone_number or "N/A")),
            "patientName": b.patient.patient_name if b.patient and b.patient.patient_name else (b.patient_name or "N/A"),
            "refNo": f"REF-{b.slot_booking_id}",
            "bookingDate": b.slot_booking_datetime.strftime('%Y-%m-%d') if b.slot_booking_datetime else (b.created_date.strftime('%Y-%m-%d') if b.created_date else "N/A"),
            "slot": b.slot.slot_name if b.slot and b.slot.slot_name else "N/A",
            "paymentMethod": b.payment_method or "N/A",
            "paymentStatus": b.payment_status or "N/A",
            "technician": b.service_provider.full_name if b.service_provider and b.service_provider.full_name else (b.service_provider.user_name if b.service_provider else "N/A"),
            "remarks": "Assigned",
            "status": b.status or "Pending",
            "files": files_count,
            "isActive": b.is_active if b.is_active is not None else True,
        })
        
    result = {
        "PendingCases": pending_bookings,
        "CompletedCases": completed_bookings,
        "Bookings": data
    }
    
    return Response({"Success": True, "result": result}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def update_booking(request):
    try:
        from services.models import Service
        data = request.data
        booking_id = data.get('booking_id')
        if not booking_id:
            return Response({"Success": False, "Message": "booking_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        booking = SlotBookingMaster.objects.get(slot_booking_id=booking_id)
        
        payment_method = data.get('payment_method', booking.payment_method)
        services = data.get('services')
        
        amount = data.get('amount')
        if not amount and services:
            amount = sum([float(s.get('price') or 0) for s in services])
        elif not amount:
            amount = booking.gross_amount

        booking.payment_method = payment_method
        booking.gross_amount = amount
        booking.net_amount = amount
        booking.save()

        if services is not None:
            SlotBookingDetails.objects.filter(slot_booking=booking).delete()
            for svc_data in services:
                service_id = svc_data.get('service_id')
                price = svc_data.get('price') or 0
                service_obj = Service.objects.get(service_id=service_id) if service_id else None
                if service_obj:
                    SlotBookingDetails.objects.create(
                        slot_booking=booking,
                        service=service_obj,
                        price=price
                    )

        return Response({"Success": True, "Message": "Booking updated successfully", "BookingID": booking.slot_booking_id}, status=status.HTTP_200_OK)
    except SlotBookingMaster.DoesNotExist:
        return Response({"Success": False, "Message": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
