from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from accounts.views import (UserTypeViewSet, UserViewSet, PermissionViewSet,
                            UsersLocationViewSet, OtpMasterViewSet,
                            send_otp, verify_otp, signup, authenticate_user,
                            forget_mpin, get_visitor_mpin, employee_login,
                            update_password)

from operations.views import (LocationViewSet, ServiceGroupViewSet, ServiceViewSet,
                              LocationServiceMappingViewSet, VisitTypeMasterViewSet,
                              PriceRateMasterViewSet, PriceRateMasterLocationsViewSet,
                              OfferMasterViewSet, OfferLocationsViewSet, OfferServiceGroupsViewSet,
                              SlotMasterViewSet, PatientViewSet, SlotBookingMasterViewSet,
                              SlotBookingDetailsViewSet, SlotBookingMasterRemarksViewSet,
                              ReportFilesDetailsViewSet, ServiceFilesDetailsViewSet,
                              get_slots, get_services_by_group, get_price, save_booking,
                              get_patient_bookings, get_all_bookings, create_order, verify_payment, get_dashboard_stats)

router = DefaultRouter()

# Accounts routes
router.register(r'user-types', UserTypeViewSet)
router.register(r'users', UserViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'users-locations', UsersLocationViewSet)
router.register(r'otp-master', OtpMasterViewSet)

# Operations routes
router.register(r'locations', LocationViewSet)
router.register(r'service-groups', ServiceGroupViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'location-service-mappings', LocationServiceMappingViewSet)
router.register(r'visit-type-master', VisitTypeMasterViewSet)
router.register(r'price-rate-master', PriceRateMasterViewSet)
router.register(r'price-rate-master-locations', PriceRateMasterLocationsViewSet)
router.register(r'offer-master', OfferMasterViewSet)
router.register(r'offer-locations', OfferLocationsViewSet)
router.register(r'offer-service-groups', OfferServiceGroupsViewSet)
router.register(r'slot-master', SlotMasterViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'slot-booking-master', SlotBookingMasterViewSet)
router.register(r'slot-booking-details', SlotBookingDetailsViewSet)
router.register(r'slot-booking-master-remarks', SlotBookingMasterRemarksViewSet)
router.register(r'report-files-details', ReportFilesDetailsViewSet)
router.register(r'service-files-details', ServiceFilesDetailsViewSet)

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
    path('api/booking/patient_bookings', get_patient_bookings, name='patient_bookings'),
    path('api/booking/all_bookings', get_all_bookings, name='all_bookings'),
    path('api/booking/dashboard_stats', get_dashboard_stats, name='dashboard_stats'),
    path('api/payment/create_order', create_order, name='create_order'),
    path('api/payment/verify', verify_payment, name='verify_payment'),
]
