import os
import sys
import urllib.request

sys.path.append(r'd:\xrai-webportal\WebPortalReact\backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webportal_core.settings')
import django
django.setup()
from django.core import signing

token = signing.dumps({'UserID': 1, 'UserType': 'Patient'})
req = urllib.request.Request('http://127.0.0.1:8000/api/locations/')
req.add_header('Authorization', 'Bearer ' + token)

try:
    response = urllib.request.urlopen(req)
    print("HTTP STATUS:", response.getcode())
    print("RESPONSE:", response.read().decode())
except Exception as e:
    print("ERROR:", e)
