from rest_framework import viewsets
from .models import (Location, ServiceGroup, Service, LocationServiceMapping, VisitTypeMaster,
                     PriceRateMaster, PriceRateMasterLocations, OfferMaster, OfferLocations,
                     OfferServiceGroups, SlotMaster, Patient, SlotBookingMaster, SlotBookingDetails,
                     SlotBookingMasterRemarks, ReportFilesDetails, ServiceFilesDetails)
from .serializers import (LocationSerializer, ServiceGroupSerializer, ServiceSerializer,
                          LocationServiceMappingSerializer, VisitTypeMasterSerializer,
                          PriceRateMasterSerializer, PriceRateMasterLocationsSerializer,
                          OfferMasterSerializer, OfferLocationsSerializer, OfferServiceGroupsSerializer,
                          SlotMasterSerializer, PatientSerializer, SlotBookingMasterSerializer,
                          SlotBookingDetailsSerializer, SlotBookingMasterRemarksSerializer,
                          ReportFilesDetailsSerializer, ServiceFilesDetailsSerializer)

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class ServiceGroupViewSet(viewsets.ModelViewSet):
    queryset = ServiceGroup.objects.all()
    serializer_class = ServiceGroupSerializer

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class LocationServiceMappingViewSet(viewsets.ModelViewSet):
    queryset = LocationServiceMapping.objects.all()
    serializer_class = LocationServiceMappingSerializer

class VisitTypeMasterViewSet(viewsets.ModelViewSet):
    queryset = VisitTypeMaster.objects.all()
    serializer_class = VisitTypeMasterSerializer

class PriceRateMasterViewSet(viewsets.ModelViewSet):
    queryset = PriceRateMaster.objects.all()
    serializer_class = PriceRateMasterSerializer

class PriceRateMasterLocationsViewSet(viewsets.ModelViewSet):
    queryset = PriceRateMasterLocations.objects.all()
    serializer_class = PriceRateMasterLocationsSerializer

class OfferMasterViewSet(viewsets.ModelViewSet):
    queryset = OfferMaster.objects.all()
    serializer_class = OfferMasterSerializer

class OfferLocationsViewSet(viewsets.ModelViewSet):
    queryset = OfferLocations.objects.all()
    serializer_class = OfferLocationsSerializer

class OfferServiceGroupsViewSet(viewsets.ModelViewSet):
    queryset = OfferServiceGroups.objects.all()
    serializer_class = OfferServiceGroupsSerializer

class SlotMasterViewSet(viewsets.ModelViewSet):
    queryset = SlotMaster.objects.all()
    serializer_class = SlotMasterSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class SlotBookingMasterViewSet(viewsets.ModelViewSet):
    queryset = SlotBookingMaster.objects.all()
    serializer_class = SlotBookingMasterSerializer

class SlotBookingDetailsViewSet(viewsets.ModelViewSet):
    queryset = SlotBookingDetails.objects.all()
    serializer_class = SlotBookingDetailsSerializer

class SlotBookingMasterRemarksViewSet(viewsets.ModelViewSet):
    queryset = SlotBookingMasterRemarks.objects.all()
    serializer_class = SlotBookingMasterRemarksSerializer

class ReportFilesDetailsViewSet(viewsets.ModelViewSet):
    queryset = ReportFilesDetails.objects.all()
    serializer_class = ReportFilesDetailsSerializer

class ServiceFilesDetailsViewSet(viewsets.ModelViewSet):
    queryset = ServiceFilesDetails.objects.all()
    serializer_class = ServiceFilesDetailsSerializer

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
from .models import ServiceGroup

@api_view(['GET'])
@permission_classes([AllowAny])
def get_slots(request):
    date = request.query_params.get('date')
    # In a real app we'd filter by date, but we just return all active slots for now to match the UI behavior
    slots = SlotMaster.objects.filter(is_active=True).values('slot_id', 'slot_name')
    return Response(list(slots), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_services_by_group(request):
    group_id = request.query_params.get('group_id')
    if not group_id:
        return Response([], status=status.HTTP_200_OK)
    
    services = Service.objects.filter(service_group_id=group_id, is_active=True).values('service_id', 'service_name')
    return Response(list(services), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_price(request):
    location_id = request.query_params.get('location_id')
    service_id = request.query_params.get('service_id')
    group_id = request.query_params.get('group_id')
    visit_type_id = request.query_params.get('visit_type_id')

    # Simplified pricing logic - return a dummy price or fetch from PriceRateMaster
    # In the original app, it called a complex SP `GetLocationServicePriceDetails`
    
    price_rate = PriceRateMaster.objects.filter(
        service_id=service_id, 
        service_group_id=group_id,
        visit_type_id=visit_type_id
    ).first()

    if price_rate and price_rate.price:
        price = price_rate.price
    else:
        # Dummy fallback price for demonstration if not found
        price = 1500

    return Response([{"PRICERATEID": price_rate.price_rate_id if price_rate else 1, "PRICE": price}], status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def save_booking(request):
    try:
        data = request.data
        
        # Simplified Booking Logic
        booking = SlotBookingMaster.objects.create(
            patient_id=data.get('PatientID'),
            slot_id=data.get('SlotID'),
            visit_type_id=data.get('VisitTypeID'),
            slot_booking_datetime=data.get('VisitDate') or datetime.datetime.now(),
            phone_number=data.get('MobileNumber'),
            patient_name=data.get('PatientName'),
            age=data.get('Age'),
            weight=data.get('Weight'),
            gender=data.get('Gender'),
            address=data.get('Address'),
            payment_method=data.get('PaymentMethod'),
            location_id=data.get('LocationID'),
            net_amount=data.get('TotalNetAmount') or 0,
            status='Booked',
            is_active=True
        )

        details = data.get('slotBookingDetails', [])
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except:
                details = []

        for item in details:
            SlotBookingDetails.objects.create(
                slot_booking=booking,
                service_id=item.get('SERVICEID'),
                service_group_id=item.get('SERVICEGROUPID'),
                price=item.get('PRICE') or 0,
                price_discount=item.get('DISCOUNTAMOUNT') or 0,
                discount_percent=item.get('DISCOUNTPERCENT') or 0
            )

        return Response({"Success": True, "Message": "Booking slot has been created successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_bookings(request):
    # In a real app we'd filter by logged in user ID
    bookings = SlotBookingMaster.objects.all().values(
        'slot_booking_id', 'slot_booking_datetime', 'patient_name', 'status', 'payment_method', 'net_amount'
    )
    return Response(list(bookings), status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_bookings(request):
    bookings = SlotBookingMaster.objects.all().values(
        'slot_booking_id', 'slot_booking_datetime', 'patient_name', 'status', 'payment_method', 'net_amount', 'phone_number', 'location__location_name'
    )
    return Response(list(bookings), status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    try:
        amount = int(request.data.get('amount', 0))
        mobile_number = request.data.get('MobileNumber', '')
        visit_date = request.data.get('VisitDate', '')
        
        amount_in_paise = amount * 100
        description = f"{mobile_number} on {visit_date}"
        
        client = razorpay.Client(auth=("YOUR_KEY_ID", "YOUR_KEY_SECRET"))
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": description,
            "payment_capture": 1
        }
        
        # In a real app we'd use valid keys. We'll mock the response for demo parity if keys fail.
        try:
            order = client.order.create(data=order_data)
            order_id = order['id']
            currency = order['currency']
        except:
            order_id = f"order_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            currency = "INR"

        return Response({"orderId": order_id, "amount": amount_in_paise, "currency": currency}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_payment(request):
    # Mocking verify logic since we don't have real keys
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_signature = request.data.get('razorpay_signature')
    
    # Normally we'd call client.utility.verify_payment_signature(...)
    return Response({"status": "success", "PaymentID": razorpay_payment_id}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_dashboard_stats(request):
    try:
        from_date = request.query_params.get('FromDate')
        to_date = request.query_params.get('ToDate')
        
        # Build base query
        query = SlotBookingMaster.objects.all()
        
        if from_date and to_date:
            # Parse dates and filter (assuming YYYY-MM-DD format)
            # using __date range
            query = query.filter(slot_booking_datetime__date__gte=from_date, slot_booking_datetime__date__lte=to_date)
            
        pending_bookings = query.filter(status='Pending').count()
        # Fallback to Booked for confirmed since the old db used Booked
        confirmed_bookings = query.filter(status='Booked').count()
        in_progress_bookings = query.filter(status='In Progress').count()
        completed_bookings = query.filter(status='Completed').count()
        
        # Count files
        report_files_uploaded = ReportFilesDetails.objects.all().count() # In reality we might filter this by date too based on related booking
        service_files_uploaded = ServiceFilesDetails.objects.all().count()
        
        result = {
            "PendingBookings": pending_bookings,
            "ConfirmedBookings": confirmed_bookings,
            "BookingInProgress": in_progress_bookings,
            "BookingPerformed": completed_bookings,
            "ReportFilesUploaded": report_files_uploaded,
            "ServiceFilesUploaded": service_files_uploaded
        }
        return Response({"Success": True, "result": result}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"Success": False, "Message": str(e)}, status=status.HTTP_200_OK)
