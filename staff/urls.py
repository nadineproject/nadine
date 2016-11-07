from django.conf.urls import url

from staff.views import activity, billing, core, member, stats, payment

urlpatterns = [
    url(r'^$', core.todo, name='staff_todo'),
    url(r'^todo/(?P<key>[^/]+)/$', core.todo_detail, name='staff_todo_detail'),
    url(r'^members/$', core.members, name='staff_members'),
    url(r'^members/(?P<group>[^/]+)/$', core.members, name='staff_member_group'),
    url(r'^bcc/(?P<group>[^/]+)/$', core.member_bcc, name='staff_group_bcc'),
    url(r'^bcc/$', core.member_bcc, name='staff_bcc'),
    url(r'^deposits/$', core.security_deposits, name='staff_deposits'),
    url(r'^export/$', core.export_users, name='staff_export_users'),
    url(r'^search/$', core.member_search, name='staff_search'),
    url(r'^user_reports/$', core.view_user_reports, name='staff_user_reports'),
    url(r'^slack_users/$', core.slack_users, name='staff_slack_users'),
    url(r'^membership/(?P<membership_id>\d+)/$', core.membership, name='staff_membership'),

    url(r'^activity/$', activity.activity, name='staff_activity'),
    url(r'^activity/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', activity.for_date, name='staff_activity_day'),
    url(r'^activity/today/$', activity.for_today, name='staff_activity_today'),
    url(r'^activity/list/$', activity.list, name='staff_activity_list'),
    url(r'^activity/user/(?P<username>[^/]+)/$', activity.for_user, name='staff_activity_user'),

    url(r'^bills/$', billing.bills, name='staff_bills'),
    url(r'^bill/list/$', billing.bill_list, name='staff_bill_list'),
    url(r'^bill/run/$', billing.run_billing, name='staff_billing_run'),
    url(r'^bill/(?P<id>\d+)/$', billing.bill, name='staff_bill'),
    url(r'^transactions/$', billing.transactions, name='staff_transactions'),
    url(r'^transaction/(?P<id>\d+)/$', billing.transaction, name='staff_transaction'),
    url(r'^pay_all/(?P<username>[^/]+)/$', billing.bills_pay_all, name='staff_bills_paid'),
    url(r'^toggle_billing_flag/(?P<username>[^/]+)/$', billing.toggle_billing_flag, name='staff_toggle_bill'),

    url(r'^detail/(?P<username>[^/]+)/$', member.detail, name='staff_user_detail'),
    # url(r'^signins/(?P<username>[^/]+)/$', member.signins, name='staff_user_signins'),
    # url(r'^signins/json/(?P<username>[^/]+)/$', member.signins_json, name='staff_json_signins'),
    url(r'^transactions/(?P<username>[^/]+)/$', member.transactions, name='staff_user_transactions'),
    url(r'^bill/(?P<username>[^/]+)/$', member.bills, name='staff_user_bills'),
    url(r'^membership/(?P<username>[^/]+)/$', member.membership, name='staff_user_membership'),
    url(r'^files/(?P<username>[^/]+)/$', member.files, name='staff_user_files'),
    # url(r'^edit/(?P<username>[^/]+)/$', member.edit, name='staff_user_edit'),

    url(r'^stats/$', stats.stats, name='staff_stats'),
    url(r'^stats/history/$', stats.history, name='staff_stats_history'),
    url(r'^stats/monthly/$', stats.monthly, name='staff_stats_monthly'),
    url(r'^stats/gender/$', stats.gender, name='staff_stats_gender'),
    url(r'^stats/neighborhood/$', stats.neighborhood, name='staff_stats_neighborhood'),
    url(r'^stats/membership-history/$', stats.membership_history, name='staff_stats_memberships'),
    url(r'^stats/membership-days/$', stats.membership_days, name='staff_stats_memberdays'),
    url(r'^stats/graph/$', stats.graph, name='staff_stats_graph'),

    url(r'^usaepay/m/$', payment.usaepay_members, name='staff_payments_members'),
    url(r'^usaepay/void/$', payment.usaepay_void, name='staff_payment_void'),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user, name='staff_user_payment'),
    url(r'^charges/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions, name='staff_charges'),
    url(r'^charges/today/$', payment.usaepay_transactions_today, name='staff_charges_today'),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user, name='staff_xero'),

    url(r'^view_ip/$', core.view_ip, name='staff_view_ip'),
    url(r'^view_config/$', core.view_config, name='view_config'),

    url(r'^event/create$', core.create_event, name='create_event'),
]

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
