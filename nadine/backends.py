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


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
