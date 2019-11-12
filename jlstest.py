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

on = Organization.objects.filter(name="Office Nomads").first()
main = Organization.objects.filter(name="312 Main").first()

# Gatekeeper Testing
# from core import *
# with open('gw_config.json', 'r') as f:
#     config = json.load(f)
#
#
# gatekeeper = Gatekeeper(config)
# gatekeeper.configure_doors()
# controller = list(gatekeeper.doors.values())[0]['controller']
# controller.load_credentials()
