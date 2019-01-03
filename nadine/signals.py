import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist

from nadine.models import Payment, BillLineItem

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BillLineItem)
def lineitem_post_save(**kwargs):
    """
    Update cached totals on UserBill.
    """
    lineitem = kwargs['instance']
    bill = lineitem.bill
    bill.update_cached_totals()


@receiver(post_delete, sender=BillLineItem)
def lineitem_post_delete(**kwargs):
    """
    Update cached totals on UserBill.
    """
    lineitem = kwargs['instance']
    try:
        bill = lineitem.bill
        bill.update_cached_totals()
    except ObjectDoesNotExist:
        logger.warn("Deleting a BillLineItem that does not have a Bill!")


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
