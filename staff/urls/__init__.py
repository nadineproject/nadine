from django.conf.urls import include, url

from staff.views import activity, billing, core, member, stats, payment, settings

urlpatterns = [
    url(r'^$', core.todo, name='todo'),
    url(r'^todo/(?P<key>[^/]+)/$', core.todo_detail, name='todo_detail'),
    url(r'^members/$', core.members, name='members'),
    url(r'^members/(?P<group>[^/]+)/$', core.members, name='member_group'),
    url(r'^bcc/(?P<group>[^/]+)/$', core.member_bcc, name='group_bcc'),
    url(r'^bcc/$', core.member_bcc, name='bcc'),
    url(r'^deposits/$', core.security_deposits, name='deposits'),
    url(r'^export/$', core.export_users, name='export_users'),
    url(r'^search/$', core.member_search, name='search'),
    url(r'^user_reports/$', core.view_user_reports, name='user_reports'),
    url(r'^slack_users/$', core.slack_users, name='slack_users'),
    url(r'^membership/(?P<membership_id>\d+)/$', core.membership, name='membership'),

    url(r'^activity/$', activity.activity, name='activity'),
    url(r'^activity/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', activity.for_date, name='activity_day'),
    url(r'^activity/today/$', activity.for_today, name='activity_today'),
    url(r'^activity/list/$', activity.list, name='activity_list'),
    url(r'^activity/user/(?P<username>[^/]+)/$', activity.for_user, name='activity_user'),

    url(r'^bills/$', billing.bills, name='bills'),
    url(r'^bill/list/$', billing.bill_list, name='bill_list'),
    url(r'^bill/run/$', billing.run_billing, name='billing_run'),
    url(r'^bill/(?P<id>\d+)/$', billing.bill, name='bill'),
    url(r'^transactions/$', billing.transactions, name='transactions'),
    url(r'^transaction/(?P<id>\d+)/$', billing.transaction, name='transaction'),
    url(r'^pay_all/(?P<username>[^/]+)/$', billing.bills_pay_all, name='bills_paid'),
    url(r'^toggle_billing_flag/(?P<username>[^/]+)/$', billing.toggle_billing_flag, name='toggle_bill'),

    url(r'^detail/(?P<username>[^/]+)/$', member.detail, name='user_detail'),
    # url(r'^signins/(?P<username>[^/]+)/$', member.signins, name='user_signins'),
    # url(r'^signins/json/(?P<username>[^/]+)/$', member.signins_json, name='json_signins'),
    url(r'^transactions/(?P<username>[^/]+)/$', member.transactions, name='user_transactions'),
    url(r'^bill/(?P<username>[^/]+)/$', member.bills, name='user_bills'),
    url(r'^membership/(?P<username>[^/]+)/$', member.membership, name='user_membership'),
    url(r'^files/(?P<username>[^/]+)/$', member.files, name='user_files'),
    # url(r'^edit/(?P<username>[^/]+)/$', member.edit, name='user_edit'),

    url(r'^stats/$', stats.stats, name='stats'),
    url(r'^stats/history/$', stats.history, name='stats_history'),
    url(r'^stats/monthly/$', stats.monthly, name='stats_monthly'),
    url(r'^stats/gender/$', stats.gender, name='stats_gender'),
    url(r'^stats/neighborhood/$', stats.neighborhood, name='stats_neighborhood'),
    url(r'^stats/membership-history/$', stats.membership_history, name='stats_memberships'),
    url(r'^stats/membership-days/$', stats.membership_days, name='stats_memberdays'),
    url(r'^stats/graph/$', stats.graph, name='stats_graph'),

    # url(r'^settings/$', settin,gs.index, namespace="settings", name='index'),
    url(r'^settings/', include('staff.urls.settings', namespace="settings")),


    url(r'^usaepay/m/$', payment.usaepay_members, name='payments_members'),
    url(r'^usaepay/void/$', payment.usaepay_void, name='payment_void'),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user, name='user_payment'),
    url(r'^charges/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions, name='charges'),
    url(r'^charges/today/$', payment.usaepay_transactions_today, name='charges_today'),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user, name='xero'),

    url(r'^view_ip/$', core.view_ip, name='view_ip'),
    url(r'^view_config/$', core.view_config, name='view_config'),

    url(r'^event/create$', core.create_event, name='create_event'),
]

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
