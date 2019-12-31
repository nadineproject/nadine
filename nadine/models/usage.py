

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist

# from nadine.models.resource import Resource

import logging

logger = logging.getLogger(__name__)


PAYMENT_CHOICES = (
    ('Bill', 'Billable'),
    ('Trial', 'Free Trial'),
    ('Waive', 'Payment Waived'),
)

class CoworkingDayManager(models.Manager):

    def billable(self):
        return self.filter(payment="Bill")

    def unbilled(self, target_date=None):
        ''' Not associated with any bill. '''
        query = self.filter(line_item__isnull=True)
        if target_date:
            # Only events prior to the given date
            return query.filter(visit_date__lte=target_date)
        return query

class CoworkingDay(models.Model):
    objects = CoworkingDayManager()
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

    @property
    def payer(self):
        # It's easy if paid_by is set
        if self.paid_by:
            return self.paid_by

        # Find out what subscriptions they had on this day
        from nadine.models.resource import Resource
        from nadine.models.membership import ResourceSubscription
        day_subscriptions = ResourceSubscription.objects.for_user_and_date(self.user, self.visit_date).filter(resource=Resource.objects.day_resource)
        if day_subscriptions:
            # This is a quick and dirty way that does not consider
            # which of these subscriptions we should use --JLS
            return day_subscriptions.first().payer

        # No one else is paying so the user is on the hook
        return self.user

    @property
    def billable(self):
        return self.payment == 'Bill'

    @property
    def waived(self):
        return self.payment == 'Waive'

    @property
    def free_trial(self):
        return self.payment == 'Trial'

    @property
    def bill(self):
        try:
            return self.line_item.bill
        except ObjectDoesNotExist:
            return None

    def mark_waived(self):
        self.payment = 'Waive'
        self.save()

    def unassociate(self):
        ''' Unassociate this day with any bill it might be added to. '''
        if self.bill:
            self.line_item.delete()

    def __str__(self):
        return '%s - %s' % (self.visit_date, self.user)

    def get_admin_url(self):
        return reverse('admin:nadine_coworkingday_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        verbose_name = "Coworking Day"
        ordering = ['-visit_date', '-created_ts']


class EventManager(models.Manager):

    def unbilled(self, target_date=None):
        ''' Not associated with any bill. '''
        query = self.filter(line_item__isnull=True)
        if target_date:
            # Only events prior to the given date
            return query.filter(start_ts__lte=target_date)
        return query


class Event(models.Model):
    objects = EventManager()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey('Room', null=True, blank=True, on_delete=models.CASCADE)
    created_ts = models.DateTimeField(auto_now_add=True)
    start_ts = models.DateTimeField(verbose_name="Start time")
    end_ts = models.DateTimeField(verbose_name="End time")
    description = models.CharField(max_length=128, null=True, blank=True)
    charge = models.DecimalField(decimal_places=2, max_digits=9, null=True, blank=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="guest_event", on_delete=models.CASCADE)
    note = models.CharField("Note", max_length=128, null=True, blank=True)
    is_public = models.BooleanField(default=False)

    @property
    def hours(self):
        ''' How many hours is this event down to 15 minutes. '''
        time_difference = self.end_ts - self.start_ts
        return time_difference.seconds/60/15/4.0

    @property
    def payer(self):
        # It's easy if paid_by is set
        if self.paid_by:
            return self.paid_by

        # Find out what subscriptions they had on this day
        from nadine.models.resource import Resource
        from nadine.models.membership import ResourceSubscription
        subscriptions = ResourceSubscription.objects.for_user_and_date(self.user, self.start_ts.date()).filter(resource=Resource.objects.event_resource)
        if subscriptions:
            # This is a quick and dirty way that does not consider
            # which of these subscriptions we should use --JLS
            return subscriptions.first().payer

        # No one else is paying so the user is on the hook
        return self.user

    @property
    def bill(self):
        if self.line_item:
            return self.line_item.bill
        return none

    def __str__(self):
        if self.description:
            return self.description
        if self.is_public:
            return "Public Event (%s)" % self.user.get_full_name()
        return "Private Event (%s)" % self.user.get_full_name()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
