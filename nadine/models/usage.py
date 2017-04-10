from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.db.models.signals import post_save

# from nadine.models.resource import Resource

import logging

logger = logging.getLogger(__name__)


PAYMENT_CHOICES = (
    ('Bill', 'Billable'),
    ('Trial', 'Free Trial'),
    ('Waive', 'Payment Waived'),
)


class CoworkingDay(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, unique_for_date="visit_date", on_delete=models.CASCADE)
    visit_date = models.DateField("Date")
    payment = models.CharField("Payment", max_length=5, choices=PAYMENT_CHOICES)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="guest_day", on_delete=models.CASCADE)
    note = models.CharField("Note", max_length=128, blank="True")
    created_ts = models.DateTimeField(auto_now_add=True)

    @property
    def guest_of(self):
        if self.paid_by:
            return self.paid_by.profile
        return None

    def __str__(self):
        return '%s - %s' % (self.visit_date, self.user)

    def get_admin_url(self):
        return reverse('admin:nadine_coworkingday_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "Coworking Day"
        ordering = ['-visit_date', '-created_ts']

def sign_in_callback(sender, **kwargs):
    log = kwargs['instance']
    from nadine.models.alerts import MemberAlert
    MemberAlert.objects.trigger_sign_in(log.user)
post_save.connect(sign_in_callback, sender=CoworkingDay)


class Event(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey('Room', null=True, on_delete=models.CASCADE)
    created_ts = models.DateTimeField(auto_now_add=True)
    start_ts = models.DateTimeField(verbose_name="Start time")
    end_ts = models.DateTimeField(verbose_name="End time")
    description = models.CharField(max_length=128, null=True)
    charge = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="guest_event", on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        if self.description:
            return self.description
        if self.is_public:
            return "Public Event (%s)" % self.user.get_full_name()
        return "Private Event (%s)" % self.user.get_full_name()


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
