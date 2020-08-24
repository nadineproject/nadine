from django.conf import settings

from .models.alerts import changing_membership_password

from nadine.models.alerts import new_membership, ending_membership

ROCKETCHAT_HOST = getattr(settings, 'ROCKETCHAT_HOST', 'demo.rocket.chat')
ROCKETCHT_ADMIN = getattr(settings, 'ROCKETCHT_ADMIN', 'user')
ROCKETCHAT_SECRET = getattr(settings, 'ROCKETCHAT_SECRET', 'pass')

ROCKETCHAT_USE_HTTPS = getattr(settings, 'ROCKETCHAT_USE_HTTPS', True)
ROCKETCHAT_SSL_IS_SIGNED = getattr(settings, 'ROCKETCHAT_SSL_IS_SIGNED', True)

ROCKETCHAT_SEND_WELCOME_MAIL = getattr(settings, 'ROCKETCHAT_SEND_WELCOME_MAIL', False)
ROCKETCHAT_REQUIRE_CHANGE_PASS = getattr(settings, 'ROCKETCHAT_REQUIRE_CHANGE_PASS', False)
ROCKETCHAT_VERIFIED_USER = getattr(settings, 'ROCKETCHAT_VERIFIED_USER', False)

ROCKETCHAT_USER_GROUP = getattr(settings, 'ROCKETCHAT_USER_GROUP', ['group1', 'group2'])
