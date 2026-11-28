from django.http import HttpResponseForbidden, JsonResponse
from django.core import signing

class BlockBrowserAPIAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            # 0. Bypass OPTIONS requests for CORS preflight
            if request.method == 'OPTIONS':
                return self.get_response(request)

            # Block internal/sensitive endpoints completely from external API
            if request.path.startswith('/api/otp-master'):
                return HttpResponseForbidden("Direct OTP table access is forbidden.")

            # 1. API URL Visible - Bypass public authentication endpoints
            if request.path.startswith('/api/auth/') or request.path.startswith('/api/technician-onboarding/submit'):
                return self.get_response(request)

            # 2. Authentication - Check for Bearer token
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return HttpResponseForbidden("Authentication credentials were not provided.")
            
            token = auth_header.split(' ')[1].strip()
            try:
                # 3. Identify user - Unsign the token with max_age (7 days)
                user_info = signing.loads(token, max_age=86400 * 7)
                request.user_info = user_info
            except (signing.BadSignature, signing.SignatureExpired):
                return HttpResponseForbidden("Invalid or expired authentication token.")
            
            # Verify UserID exists in payload
            if not user_info.get('UserID'):
                return HttpResponseForbidden("Malformed authentication token.")
            
            # 4. Authorization - Check what THIS user is allowed to do
            user_type = str(request.user_info.get('UserType', '')).strip().lower()
            
            if user_type == 'patient':
                # Block admin-only endpoints under /api/booking
                if (request.path.startswith('/api/booking/all_bookings') or 
                    request.path.startswith('/api/booking/dashboard_stats') or 
                    request.path.startswith('/api/booking/technician_bookings')):
                    return HttpResponseForbidden("Access restricted to administrative staff.")

                # Allowed paths for Patient
                allowed_paths = [
                    '/api/booking',
                    '/api/payment',
                    '/api/locations',
                    '/api/service-groups',
                    '/api/services',
                    '/api/patients',
                    '/api/offer-master',
                    '/api/user-types',
                    '/api/tracking',
                    '/api/dpdp-consents/my-consent'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, patients can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services', '/api/offer-master', '/api/user-types']:
                            if request.method == 'GET':
                                is_allowed = True
                        else:
                            is_allowed = True
                        break
                
                if not is_allowed:
                    return HttpResponseForbidden("You do not have permission to access this resource.")
            
            elif user_type == 'admin':
                # Admins have access to operational resources, but not SuperAdmin consent governance or Consultant Admin
                if request.path.startswith('/api/dpdp-consents'):
                    return HttpResponseForbidden("SuperAdmin access required.")
                if request.path.startswith('/api/consultant/submissions'):
                    return HttpResponseForbidden("Consultant Admin access required.")
                pass

            elif user_type == 'superadmin':
                # SuperAdmins strictly have access to DPDP consent governance resources
                allowed_paths = [
                    '/api/dpdp-consents',
                    '/api/tracking'
                ]
                is_allowed = any(request.path.startswith(path) for path in allowed_paths)
                if not is_allowed:
                    return HttpResponseForbidden("Admin operational access required.")

            elif user_type in ['consultant admin', 'consultant_admin', 'consultantadmin']:
                # Dedicated Consultant Admin role: manages consultant evaluations, dossiers, and doctor accounts
                allowed_paths = [
                    '/api/consultant/submissions',
                    '/api/users',
                    '/api/user-types',
                    '/api/tracking'
                ]
                is_allowed = any(request.path.startswith(path) for path in allowed_paths)
                if not is_allowed:
                    return HttpResponseForbidden("Consultant Admin does not have permission to access operational clinic resources.")

            elif user_type in ['technician admin', 'technician_admin', 'technicianadmin']:
                # Dedicated Technician Admin role: manages technician onboarding applications, rates, and tracking
                allowed_paths = [
                    '/api/technician-onboarding/admin',
                    '/api/tracking',
                    '/api/users',
                    '/api/locations',
                ]
                is_allowed = any(request.path.startswith(path) for path in allowed_paths)
                if not is_allowed:
                    return HttpResponseForbidden("Technician Admin does not have permission to access this resource.")

            elif user_type == 'consultant':
                # Allowed paths for Consultant exam portal
                allowed_paths = [
                    '/api/consultant/exam',
                    '/api/tracking'
                ]
                is_allowed = any(request.path.startswith(path) for path in allowed_paths)
                if not is_allowed:
                    return HttpResponseForbidden("You do not have permission to access this resource.")


            
            elif user_type == 'technician':
                # Block admin-only endpoints under /api/booking
                if (request.path.startswith('/api/booking/all_bookings') or 
                    request.path.startswith('/api/booking/dashboard_stats')):
                    return HttpResponseForbidden("Access restricted to administrative staff.")

                # Allowed paths for Technician
                allowed_paths = [
                    '/api/booking',
                    '/api/locations',
                    '/api/service-groups',
                    '/api/services',
                    '/api/offer-master',
                    '/api/user-types',
                    '/api/tracking'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, technicians can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services', '/api/offer-master', '/api/user-types']:
                            if request.method == 'GET':
                                is_allowed = True
                        else:
                            is_allowed = True
                        break
                
                if not is_allowed:
                    return HttpResponseForbidden("You do not have permission to access this resource.")
            
            elif user_type == 'partner':
                # Allowed paths for Partner
                allowed_paths = [
                    '/api/booking',
                    '/api/payment',
                    '/api/locations',
                    '/api/service-groups',
                    '/api/services',
                    '/api/patients',
                    '/api/offer-master',
                    '/api/user-types',
                    '/api/tracking'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, partners can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services', '/api/offer-master', '/api/user-types']:
                            if request.method == 'GET':
                                is_allowed = True
                        else:
                            is_allowed = True
                        break
                
                if not is_allowed:
                    return HttpResponseForbidden("You do not have permission to access this resource.")
            
            else:
                return HttpResponseForbidden("Unknown user role.")

            # 5. Return only permitted data (Handled by passing to the view)
        return self.get_response(request)
