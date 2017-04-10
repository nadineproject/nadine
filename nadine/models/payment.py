from __future__ import unicode_literals

import logging

from datetime import datetime, time, date, timedelta

from django.db import models
from django.db.models import Q
from django.contrib import admin
from django.core import urlresolvers
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings

logger = logging.getLogger(__name__)


class BillingLog(models.Model):

    """A record of when the billing was last calculated and whether it was successful"""
    started = models.DateTimeField(auto_now_add=True)
    ended = models.DateTimeField(blank=True, null=True)
    successful = models.BooleanField(default=False)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'nadine'
        ordering = ['-started']
        get_latest_by = 'started'

    def __str__(self):
        return 'BillingLog %s: %s' % (self.started, self.successful)

    def ended_date(self):
        if not self.ended:
            return None
        return datetime.date(self.ended)


class OldBill(models.Model):

    """A record of what fees a Member owes."""
    bill_date = models.DateField(blank=False, null=False)
    user = models.ForeignKey(User, related_name="old_bill", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    membership = models.ForeignKey('OldMembership', blank=True, null=True, on_delete=models.CASCADE)
    dropins = models.ManyToManyField('CoworkingDay', related_name='bills')
    guest_dropins = models.ManyToManyField('CoworkingDay', related_name='guest_bills')
    new_member_deposit = models.BooleanField(default=False, blank=False, null=False)
    paid_by = models.ForeignKey(User, blank=True, null=True, related_name='guest_bills', on_delete=models.CASCADE)
    in_progress = models.BooleanField(default=False, blank=False, null=False)

    @property
    def overage_days(self):
        days = self.dropins.count() + self.guest_dropins.count()
        if self.membership and self.membership.dropin_allowance < days:
            return days - self.membership.dropin_allowance
        return 0

    class Meta:
        app_label = 'nadine'
        ordering = ['-bill_date']
        get_latest_by = 'bill_date'

    def __str__(self):
        return 'Old Bill %s [%s]: %s - $%s' % (self.id, self.bill_date, self.user, self.amount)

    def get_admin_url(self):
        return urlresolvers.reverse('admin:nadine_bill_change', args=[self.id])


class Transaction(models.Model):

    """A record of charges for a user."""
    transaction_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    TRANSACTION_STATUS_CHOICES = (('open', 'Open'), ('closed', 'Closed'))
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, blank=False, null=False, default='open')
    bills = models.ManyToManyField(OldBill, related_name='transactions')
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'nadine'
        ordering = ['-transaction_date']

    def __str__(self):
        return '%s: %s' % (self.user.get_full_name(), self.amount)

    def get_admin_url(self):
        return urlresolvers.reverse('admin:nadine_transaction_change', args=[self.id])
