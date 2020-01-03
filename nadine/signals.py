import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from nadine import email
from nadine.models import Payment, BillLineItem
from nadine.models.alerts import sign_in, new_membership, ending_membership, change_membership
from nadine.models.usage import CoworkingDay
from nadine.utils.payment_api import PaymentAPI
from nadine.utils.slack_api import SlackAPI

logger = logging.getLogger(__name__)


#####################################################################
# Call Backs for Notifications
#####################################################################


@receiver(sign_in)
def notify_sign_in(sender, **kwargs):
    user = kwargs['user']
    # Send out a bunch of things the first time they sign in
    if CoworkingDay.objects.filter(user=user).count() == 1:
        try:
            email.announce_free_trial(user)
        except:
            logger.error("Could not announce free trial for %s" % user.email)
        try:
            email.send_introduction(user)
        except:
            logger.error("Could not send introduction email to %s" % user.email)
        try:
            email.subscribe_to_newsletter(user)
        except:
            logger.error("Could not subscribe user to email: %s" % user.email)
    else:
        # If it's not their first day and they still have open alerts, message the team
        if len(user.profile.open_alerts()) > 0:
            email.send_manage_member(user)


@receiver(new_membership)
def notify_new_membership(sender, **kwargs):
    user = kwargs['user']

    # Notify the user
    try:
        email.send_new_membership(user)
    except Exception as e:
        logger.error(f"Could not send New Member notification for '{user}'" , e)

    # Notify the team
    try:
        email.announce_new_membership(user)
    except Exception as e:
        logger.error(f"Could not send announce new member '{user}'" , e)

    # Invite them to slack
    if hasattr(settings, 'SLACK_API_TOKEN'):
        SlackAPI().invite_user_quiet(user)


@receiver(ending_membership)
def notify_ending_membership(sender, **kwargs):
    user = kwargs['user']
    end = user.membership.end_date
    subject = "Exiting Member: %s/%s/%s" % (end.month, end.day, end.year)
    email.send_manage_member(user, subject=subject)


#####################################################################
# Call Backs for Bills and Payments
#####################################################################


@receiver(change_membership)
def disable_billing(sender, **kwargs):
    # Turn off automatic billing when
    # ANY change is made to the membership
    user = kwargs['user']
    payment_api = PaymentAPI()
    if payment_api.enabled:
        payment_api.disable_recurring(user.username)


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


# Copyright 2020 The Nadine Project (https://nadineproject.org/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
