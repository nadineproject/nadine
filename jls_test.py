from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.utils.timezone import localtime, now
from django.db.models import Q, Count, Sum, Value
from django.db.models.functions import Coalesce

from nadine.models import *

today = localtime(now()).date()
yesterday = today - timedelta(days=1)
tomorrow = today + timedelta(days=1)
one_month_from_now = today + relativedelta(months=1)
one_month_ago = today - relativedelta(months=1)
two_months_ago = today - relativedelta(months=2)

target_date = today

jacob = User.objects.get(username='jacob')
j = jacob
user = jacob

on = Organization.objects.get(name="Office Nomads")

# Make sure you've run the old billing engine first
# ./manage run_billing
def test_new_bills():
    for old in OldBill.objects.all().order_by('bill_date').reverse():
        user = old.user
        user.membership.generate_bill()
        print("User: %s" % (user))
        print("   OLD: Date: %s, Amount: $%s" % (old.bill_date, old.amount))
        new = user.bills.last()
        if new:
            print("   NEW: Date: %s, Amount: $%s" % (new.due_date, new.amount))
