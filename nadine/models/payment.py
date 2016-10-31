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
from django.utils import timezone

from nadine.models.core import *

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

    def __unicode__(self):
        return 'BillingLog %s: %s' % (self.started, self.successful)

    def ended_date(self):
        if not self.ended:
            return None
        return datetime.date(self.ended)


class Bill(models.Model):

    """A record of what fees a Member owes."""
    bill_date = models.DateField(blank=False, null=False)
    user = models.ForeignKey(User)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    membership = models.ForeignKey('Membership', blank=True, null=True)
    dropins = models.ManyToManyField('CoworkingDay', related_name='bills')
    guest_dropins = models.ManyToManyField('CoworkingDay', related_name='guest_bills')
    new_member_deposit = models.BooleanField(default=False, blank=False, null=False)
    paid_by = models.ForeignKey(User, blank=True, null=True, related_name='guest_bills')

    def overage_days(self):
        return self.dropins.count() - self.membership.dropin_allowance

    class Meta:
        app_label = 'nadine'
        ordering = ['-bill_date']
        get_latest_by = 'bill_date'

    def __unicode__(self):
        return 'Bill %s [%s]: %s - $%s' % (self.id, self.bill_date, self.user, self.amount)

    def get_admin_url(self):
        return urlresolvers.reverse('admin:nadine_bill_change', args=[self.id])


class Transaction(models.Model):

    """A record of charges for a user."""
    transaction_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    TRANSACTION_STATUS_CHOICES = (('open', 'Open'), ('closed', 'Closed'))
    status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, blank=False, null=False, default='open')
    bills = models.ManyToManyField(Bill, related_name='transactions')
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'nadine'
        ordering = ['-transaction_date']

    def __unicode__(self):
        return '%s: %s' % (self.user.get_full_name(), self.amount)

    def get_admin_url(self):
        return urlresolvers.reverse('admin:nadine_transaction_change', args=[self.id])
