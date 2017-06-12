from django.shortcuts import redirect
from django.conf.urls import include, url

from staff.views import core

from staff.views import billing, payment

app_name = 'staff'
urlpatterns = [
    # Pages
    url(r'^bills/$', billing.bill_list, name='bills'),
    url(r'^bill/(?P<bill_id>\d+)/$', billing.bill_view, name='bill'),
    url(r'^bills/outstanding/$', billing.outstanding, name='outstanding'),
    url(r'^bills/(?P<username>[^/]+)/$', billing.user_bills, name='user_bills'),
    url(r'^daily/$', billing.billing_today, name='billing_today'),
    url(r'^daily/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', billing.daily_billing, name='daily_billing'),

    # Actions
    url(r'^pay_user/(?P<username>[^/]+)/$', billing.set_user_paid, name='user_paid'),
    url(r'^pay_bill/(?P<bill_id>\d+)/$', billing.set_bill_paid, name='bill_paid'),
    url(r'^toggle_billing_flag/(?P<username>[^/]+)/$', billing.toggle_billing_flag, name='billing_flag'),
    url(r'^toggle_bill_in_progress/(?P<bill_id>\d+)/$', billing.toggle_bill_in_progress, name='bill_in_progress'),
    url(r'^generate_bill/(?P<membership_id>[^/]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', billing.generate_bill, name='generate_bill'),

    # Integerations
    url(r'^usaepay/m/$', payment.usaepay_members, name='payments_members'),
    url(r'^usaepay/void/$', payment.usaepay_void, name='payment_void'),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user, name='user_payment'),
    url(r'^charges/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions, name='charges'),
    url(r'^charges/today/$', payment.usaepay_transactions_today, name='charges_today'),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user, name='xero'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
