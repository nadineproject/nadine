from django.utils.timezone import localtime, now

from nadine.models.billing import SubscriptionLineItem, EventLineItem, CoworkingDayLineItem
from nadine.models.resource import Resource
from nadine.models.membership import IndividualMembership, ResourceSubscription
from nadine.models.usage import CoworkingDay, Event

today = localtime(now()).date()

def create(instance):
    instance.save()
    return instance

def a_subscription(membership, resource=None, start_date=today, monthly_rate=100, overage_rate=20):
    if resource is None:
        resource = Resource.objects.day_resource
    return ResourceSubscription(
        membership=membership, resource=resource, start_date=start_date,
        monthly_rate=monthly_rate, overage_rate=overage_rate
    )

def a_subscriptionlineitem(bill, membership, amount=100, resource=None):
    return SubscriptionLineItem(
        subscription=create(a_subscription(membership, resource=resource)),
        bill=bill,
        amount=amount
    )

def a_coworkingday(user, visit_date=today, payment="Bill"):
    return CoworkingDay(user=user, visit_date=visit_date, payment=payment)

def a_coworkingdaylineitem(bill, user, amount=50, visit_date=today, day=None):
    if day is None:
        day = create(a_coworkingday(user, visit_date))
    return CoworkingDayLineItem(
        day=day,
        bill=bill,
        amount=amount
    )

def an_event(user, start_ts, end_ts):
    return Event(user=user, start_ts=start_ts, end_ts=end_ts)

def an_eventlineitem(bill, user, start_ts, end_ts, amount=300, event=None):
    if event is None:
        event = create(an_event(user, start_ts, end_ts))
    return EventLineItem(
        event=event,
        bill=bill,
        amount=amount
    )