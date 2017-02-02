from django.shortcuts import redirect
from django.conf.urls import include, url

from staff.views import core

from staff.views import billing, payment

urlpatterns = [
    url(r'^bills/$', billing.bills, name='bills'),
    url(r'^bill/list/$', billing.bill_list, name='bill_list'),
    url(r'^bill/(?P<id>\d+)/$', billing.bill, name='bill'),
    url(r'^transactions/$', billing.transactions, name='transactions'),
    url(r'^transaction/(?P<id>\d+)/$', billing.transaction, name='transaction'),
    url(r'^pay_all/(?P<username>[^/]+)/$', billing.bills_pay_all, name='bills_paid'),
    url(r'^run/$', billing.run_billing, name='run'),
    url(r'^toggle_billing_flag/(?P<username>[^/]+)/$', billing.toggle_billing_flag, name='toggle_bill'),

    url(r'^bills/(?P<username>[^/]+)/$', billing.user_bills, name='user_bills'),
    url(r'^transactions/(?P<username>[^/]+)/$', billing.user_transactions, name='user_transactions'),

    url(r'^usaepay/m/$', payment.usaepay_members, name='payments_members'),
    url(r'^usaepay/void/$', payment.usaepay_void, name='payment_void'),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user, name='user_payment'),
    url(r'^charges/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions, name='charges'),
    url(r'^charges/today/$', payment.usaepay_transactions_today, name='charges_today'),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user, name='xero'),
]

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
