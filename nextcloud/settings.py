from django.conf import settings

from .models.alerts import changing_membership_password

from nadine.models.alerts import new_membership, ending_membership

NEXTCLOUD_HOST = getattr(settings, 'NEXTCLOUD_HOST', 'cloud.example.com')
NEXTCLOUD_ADMIN = getattr(settings, 'NEXTCLOUD_ADMIN', 'admin')
NEXTCLOUD_PASSWORD = getattr(settings, 'NEXTCLOUD_SECRET', 'password')

NEXTCLOUD_USE_HTTPS = getattr(settings, 'NEXTCLOUD_USE_HTTPS', True)
NEXTCLOUD_SSL_IS_SIGNED = getattr(settings, 'NEXTCLOUD_SSL_IS_SIGNED', True)

NEXTCLOUD_USER_DEFAULT_PASSWORD = getattr(settings, 'NEXTCLOUD_USER_DEFAULT_PASSWORD', None)
NEXTCLOUD_USER_SEND_EMAIL_PASSWORD = getattr(settings, 'NEXTCLOUD_USER_SEND_EMAIL_PASSWORD', False)
NEXTCLOUD_USER_GROUP = getattr(settings, 'NEXTCLOUD_USER_GROUP', None)
NEXTCLOUD_USER_QUOTA = getattr(settings, 'NEXTCLOUD_USER_QUOTA', '100GB')
