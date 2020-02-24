from django.urls import path

from staff.views import core
from staff.views import billing, payment


app_name = 'staff'
urlpatterns = [
    # Pages
    path('bills/', billing.bill_list, name='bills'),
    path('bill/<int:bill_id>/', billing.bill_view, name='bill'),
    path('bill_redirect/', billing.bill_view_redirect, name='bill_redirect'),
    path('bills/outstanding/', billing.outstanding, name='outstanding'),
    path('bills/<username>/', billing.user_bills, name='user_bills'),
    path('batch_logs/', billing.batch_logs, name='batch_logs'),

    # Actions
    path('bill_paid/<int:bill_id>/', billing.action_bill_paid, name='bill_paid'),
    path('billing_flag/<username>/', billing.action_billing_flag, name='billing_flag'),
    path('bill_delay/<bill_id>/', billing.action_bill_delay, name='bill_delay'),
    path('record_payment/', billing.action_record_payment, name='record_payment'),

    # Integerations
    path('usaepay/m/', payment.usaepay_members, name='payments_members'),
    path('usaepay/void/', payment.usaepay_void, name='payment_void'),
    path('usaepay/<username>/', payment.usaepay_user, name='user_payment'),
    path('charges/<int:year>/<int:month>/<int:day>/', payment.usaepay_transactions, name='charges'),
    path('charges/today/', payment.usaepay_transactions_today, name='charges_today'),
    path('xero/<username>/', payment.xero_user, name='xero'),
]

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
