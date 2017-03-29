from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.utils.timezone import localtime, now

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
