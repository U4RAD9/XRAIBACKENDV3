from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from users.views import (UserViewSet,
                            send_otp, verify_otp, signup, authenticate_user,
                            forget_mpin, get_visitor_mpin, employee_login,
                            update_password)
from user_type.views import UserTypeViewSet
from otp_master.views import OtpMasterViewSet
from locations.views import LocationViewSet
from service_group.views import ServiceGroupViewSet
from services.views import ServiceViewSet, get_services_by_group
from price_rate_master.views import PriceRateMasterViewSet, PriceRateMasterLocationViewSet
from offer_master.views import OfferMasterViewSet
from patients.views import PatientViewSet
from slots.views import SlotMasterViewSet, get_slots
from bookings.views import (SlotBookingMasterViewSet, SlotBookingDetailsViewSet,
                              get_price, save_booking, update_booking, get_patient_bookings, get_last_booking,
                              get_all_bookings, get_booking_details, upload_booking_file, create_order, verify_payment, get_dashboard_stats, get_technician_bookings, upload_prescription_file, update_booking_status, update_payment_status)

router = DefaultRouter()

# Accounts routes
router.register(r'user-types', UserTypeViewSet)
router.register(r'users', UserViewSet)
router.register(r'otp-master', OtpMasterViewSet)

# Operations routes
router.register(r'locations', LocationViewSet)
router.register(r'service-groups', ServiceGroupViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'price-rate-master', PriceRateMasterViewSet)
router.register(r'price-rate-master-locations', PriceRateMasterLocationViewSet)
router.register(r'offer-master', OfferMasterViewSet)

router.register(r'slot-master', SlotMasterViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'slot-booking-master', SlotBookingMasterViewSet)
router.register(r'slot-booking-details', SlotBookingDetailsViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/send_otp', send_otp, name='send_otp'),
    path('api/auth/verify_otp', verify_otp, name='verify_otp'),
    path('api/auth/signup', signup, name='signup'),
    path('api/auth/login', authenticate_user, name='login'),
    path('api/auth/employee_login', employee_login, name='employee_login'),
    path('api/auth/forget_mpin', forget_mpin, name='forget_mpin'),
    path('api/auth/update_password', update_password, name='update_password'),
    path('api/auth/get_visitor_mpin', get_visitor_mpin, name='get_visitor_mpin'),
    path('api/booking/get_slots', get_slots, name='get_slots'),
    path('api/booking/get_services', get_services_by_group, name='get_services'),
    path('api/booking/get_price', get_price, name='get_price'),
    path('api/booking/save', save_booking, name='save_booking'),
    path('api/booking/update', update_booking, name='update_booking'),
    path('api/booking/patient_bookings', get_patient_bookings, name='patient_bookings'),
    path('api/booking/get_last_booking', get_last_booking, name='get_last_booking'),
    path('api/booking/details/<int:id>', get_booking_details, name='get_booking_details'),
    path('api/booking/upload_file/<int:id>', upload_booking_file, name='upload_booking_file'),
    path('api/booking/upload_prescription/<int:id>', upload_prescription_file, name='upload_prescription_file'),
    path('api/booking/update_booking_status/<int:id>', update_booking_status, name='update_booking_status'),
    path('api/booking/update_payment_status/<int:id>', update_payment_status, name='update_payment_status'),
    path('api/booking/all_bookings', get_all_bookings, name='all_bookings'),
    path('api/booking/technician_bookings', get_technician_bookings, name='technician_bookings'),
    path('api/booking/dashboard_stats', get_dashboard_stats, name='dashboard_stats'),
    path('api/payment/create_order', create_order, name='create_order'),
    path('api/payment/verify', verify_payment, name='verify_payment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
