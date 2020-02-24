from django.db import models
from django.conf import settings
from django.utils.functional import cached_property

class LDAPAccountStatus(models.Model):
    """
    Model to keep track of individual LDAP failures in Django's database.
    There's likely potential for a race condition here but I figure it's just
    for reporting and therefore fairly innocuous - better than nothing.

    TODO: This needs to be renamed to something a little less confusing.
    """
    objects = models.Manager()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL
    )
    synchronized = models.BooleanField(default=False)
    ldap_error_message = models.CharField(max_length=255, blank=True)
    ldap_uid = models.CharField(unique=True, max_length=255, blank=True, null=True)
    ldap_dn = models.CharField(unique=True, max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.user:
            self.ldap_uid = ldap_uid(self.user.pk)
        super(LDAPAccountStatus, self).save(*args, **kwargs)

def ldap_uid(id):
    return "nadine_user_{}".format(id)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
