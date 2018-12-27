from django.conf import settings
from django.contrib.auth.models import User


class EmailOrUsernameModelBackend(object):

    def authenticate(self, request, username=None, password=None):
        try:
            username = username.lower()
            if '@' in username:
                user = User.helper.by_email(username)
            else:
                user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
