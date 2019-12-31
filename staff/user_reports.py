from django import forms
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.utils.timezone import localtime, now
from nadine.models.membership import Membership
from arpwatch.models import UserDevice
from django.forms.widgets import SelectDateWidget
from dateutil.relativedelta import relativedelta


REPORT_KEYS = (
    ('NEW_USERS', 'New Users'),
    ('NEW_MEMBER', 'New Memberships'),
    ('EXITING_MEMBER', 'Ending Memberships'),
    ('INVALID_BILLING', 'Users with Invalid Billing'),
    ('NO_DEVICE', 'Users with no Registered Devices'),
)

REPORT_FIELDS = (
    ('FIRST', 'First Name'),
    ('LAST', 'Last Name'),
    ('JOINED', 'Date Joined'),
    #('LAST', 'Last Visit'),
)


def getDefaultForm():
    start = localtime(now()).date() - relativedelta(months=1)
    end = localtime(now()).date()
    form_data = {'report': 'NEW_MEMBER', 'order_by': 'JOINED', 'active_only': False, 'start_date': start, 'end_date': end}
    return UserReportForm(form_data)


class UserReportForm(forms.Form):
    years = (2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016)
    report = forms.ChoiceField(choices=REPORT_KEYS, required=True)
    order_by = forms.ChoiceField(choices=REPORT_FIELDS, required=True)
    active_only = forms.BooleanField(initial=True, required=False)
    #start_date = forms.DateField(required=True, widget=SelectDateWidget(years=years))
    #end_date = forms.DateField(required=True, widget=SelectDateWidget(years=years))
    start_date = forms.DateField(required=True)
    end_date = forms.DateField(required=True)


class User_Report:

    def __init__(self, form):
        self.report = form.data['report']
        self.order_by = form.data['order_by']
        self.active_only = 'active_only' in form.data
        self.start_date = form.data['start_date']
        self.end_date = form.data['end_date']
        if not self.end_date:
            self.end_date = localtime(now()).date()

    def get_users(self):
        # Grab the users we want
        users = None
        if self.report == "NEW_USERS":
            users = self.new_users()
        elif self.report == "NEW_MEMBER":
            users = self.new_membership()
        elif self.report == "EXITING_MEMBER":
            users = self.ended_membership()
        elif self.report == "INVALID_BILLING":
            users = self.invalid_billing()
        elif self.report == "NO_DEVICE":
            users = self.no_device()
        if not users:
            return User.objects.none()

        # Only active members?
        if self.active_only:
            users = users.filter(id__in=User.helper.active_members())

        # Sort them
        if self.order_by == "FIRST":
            users = users.order_by("first_name")
        elif self.order_by == "LAST":
            users = users.order_by("last_name")
        elif self.order_by == "JOINED":
            users = users.order_by("date_joined")

        # Done!
        return users

    def new_users(self):
        return User.objects.filter(date_joined__gte=self.start_date, date_joined__lte=self.end_date)

    def new_membership(self):
        new_memberships = Membership.objects.date_range(start=self.start_date, end=self.end_date, action='started')
        return User.objects.filter(membership__id__in=new_memberships)

    def ended_membership(self):
        ended_memberships = Membership.objects.date_range(start=self.start_date, end=self.end_date, action='ended')
        new_memberships = Membership.objects.date_range(start=self.start_date, end=self.end_date, action='started')
        return User.objects.filter(membership__id__in=ended_memberships).exclude(membership__id__in=new_memberships)

    def invalid_billing(self):
        return User.objects.filter(profile__valid_billing=False)

    def no_device(self):
        devices = UserDevice.objects.filter(user__isnull=False)
        users = User.objects.filter(date_joined__gte=self.start_date, date_joined__lte=self.end_date)
        return users.exclude(pk__in=devices.values('user'))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
