from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from django.core import urlresolvers
from django.db.models.signals import post_save

import logging

logger = logging.getLogger(__name__)


PAYMENT_CHOICES = (
    ('Bill', 'Billable'),
    ('Trial', 'Free Trial'),
    ('Waive', 'Payment Waived'),
)


class CoworkingDay(models.Model):
    user = models.ForeignKey(User, unique_for_date="visit_date")
    visit_date = models.DateField("Date")
    payment = models.CharField("Payment", max_length=5, choices=PAYMENT_CHOICES)
    paid_by = models.ForeignKey(User, blank=True, null=True, related_name="guest_day")
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
        return urlresolvers.reverse('admin:nadine_coworkingday_change', args=[self.id])

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
    user = models.ForeignKey(User)
    room = models.ForeignKey('Room', null=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    start_ts = models.DateTimeField(verbose_name="Start time")
    end_ts = models.DateTimeField(verbose_name="End time")
    description = models.CharField(max_length=128, null=True)
    charge = models.DecimalField(decimal_places=2, max_digits=9, null=True)
    paid_by = models.ForeignKey(User, blank=True, null=True, related_name="guest_event")
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        if self.description:
            return self.description
        if self.is_public:
            return "Public Event (%s)" % user.get_full_name()
        return "Private Event (%s)" % user.get_full_name()
