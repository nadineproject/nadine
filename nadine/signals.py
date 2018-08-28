from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from nadine.models import Payment

@receiver(post_save, sender=Payment)
def payment_post_save(**kwargs):
    """
    Update cached totals on UserBill.
    """
    payment = kwargs['instance']
    bill = payment.bill
    bill.update_cached_totals()

@receiver(post_delete, sender=Payment)
def payment_post_delete(**kwargs):
    """
    Update cached totals on UserBill.
    """
    payment = kwargs['instance']
    bill = payment.bill
    bill.update_cached_totals()
