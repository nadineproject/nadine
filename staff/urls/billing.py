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
    url(r'^batch_logs/$', billing.batch_logs, name='batch_logs'),

    # Actions
    url(r'^bill_paid/(?P<bill_id>\d+)/$', billing.action_bill_paid, name='bill_paid'),
    url(r'^billing_flag/(?P<username>[^/]+)/$', billing.action_billing_flag, name='billing_flag'),
    url(r'^bill_delay/(?P<bill_id>\d+)/$', billing.action_bill_delay, name='bill_delay'),
    url(r'^record_payment/$', billing.action_record_payment, name='record_payment'),

    # Integerations
    url(r'^usaepay/m/$', payment.usaepay_members, name='payments_members'),
    url(r'^usaepay/void/$', payment.usaepay_void, name='payment_void'),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user, name='user_payment'),
    url(r'^charges/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions, name='charges'),
    url(r'^charges/today/$', payment.usaepay_transactions_today, name='charges_today'),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user, name='xero'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
