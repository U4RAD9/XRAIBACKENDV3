from django.http import HttpResponseForbidden
from django.core import signing

class BlockBrowserAPIAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            # 0. Bypass OPTIONS requests for CORS preflight
            if request.method == 'OPTIONS':
                return self.get_response(request)

            # 1. API URL Visible - Bypass public authentication endpoints
            if request.path.startswith('/api/auth/'):
                return self.get_response(request)

            # 2. Authentication - Check for Bearer token
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return HttpResponseForbidden("Authentication credentials were not provided.")
            
            token = auth_header.split(' ')[1]
            try:
                # 3. Identify user - Unsign the token
                user_info = signing.loads(token)
                request.user_info = user_info
            except signing.BadSignature:
                return HttpResponseForbidden("Invalid or expired authentication token.")
            
            # 4. Authorization - Check what THIS user is allowed to do
            user_type = request.user_info.get('UserType', '').strip().lower()
            
            if user_type == 'patient':
                # Allowed paths for Patient
                allowed_paths = [
                    '/api/booking',
                    '/api/payment',
                    '/api/locations',
                    '/api/service-groups',
                    '/api/services',
                    '/api/patients'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, patients can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services']:
                            if request.method == 'GET':
                                is_allowed = True
                        else:
                            is_allowed = True
                        break
                
                if not is_allowed:
                    return HttpResponseForbidden("You do not have permission to access this resource.")
            
            elif user_type == 'admin':
                # Admins have access to everything
                pass
            
            elif user_type == 'technician':
                # Allowed paths for Technician
                allowed_paths = [
                    '/api/booking',
                    '/api/locations',
                    '/api/service-groups',
                    '/api/services'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, technicians can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services']:
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
                    '/api/patients'
                ]
                
                is_allowed = False
                for path in allowed_paths:
                    if request.path.startswith(path):
                        # For master tables, partners can only read (GET)
                        if path in ['/api/locations', '/api/service-groups', '/api/services']:
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
