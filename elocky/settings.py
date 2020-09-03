from django.conf import settings

from nadine.models.alerts import new_membership, ending_membership

ELOCKY_API_CLIENT_ID = getattr(settings, 'ELOCKY_API_CLIENT_ID', 'api_client_id')
ELOCKY_API_CLIENT_SECRET = getattr(settings, 'ELOCKY_API_CLIENT_SECRET', 'api_client_secret')
ELOCKY_USERNAME = getattr(settings, 'ELOCKY_USERNAME', 'admin')
ELOCKY_PASSWORD = getattr(settings, 'ELOCKY_SECRET', 'password')

CRYPTOGRAPHY_KEY = getattr(settings, 'CRYPTOGRAPHY_KEY', None)
