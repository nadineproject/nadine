from django.conf.urls import url

from staff.views import activity, billing, core, member, stats, payment

urlpatterns = [
    url(r'^$', core.todo),
    url(r'^todo/(?P<key>[^/]+)/$', core.todo_detail),
    url(r'^members/$', core.members),
    url(r'^members/(?P<group>[^/]+)/$', core.members),
    url(r'^bcc/(?P<group>[^/]+)/$', core.member_bcc),
    url(r'^deposits/$', core.security_deposits),
    url(r'^export/$', core.export_members),
    url(r'^bcc/$', core.member_bcc),
    url(r'^search/$', core.member_search),
    url(r'^user_reports/$', core.view_user_reports),
    url(r'^slack_users/$', core.slack_users),
    url(r'^ip/$', core.view_ip),
    url(r'^membership/(?P<membership_id>\d+)/$', core.membership),

    url(r'^activity/$', activity.activity),
    url(r'^activity/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', activity.for_date),
    url(r'^activity/today/$', activity.for_today),
    url(r'^activity/list/$', activity.list),
    url(r'^activity/user/(?P<username>[^/]+)/$', activity.for_user),

    url(r'^bill/$', billing.bills),
    url(r'^bill/list/$', billing.bill_list),
    url(r'^bill/run/$', billing.run_billing),
    url(r'^bill/(?P<id>\d+)/$', billing.bill),
    url(r'^transaction/$', billing.transactions),
    url(r'^transaction/(?P<id>\d+)/$', billing.transaction),
    url(r'^pay_all/(?P<username>[^/]+)/$', billing.bills_pay_all),
    url(r'^(?P<member_id>\d+)/toggle_billing_flag/$', billing.toggle_billing_flag),

    url(r'^u/(?P<username>[^/]+)/$', member.detail_user),
    url(r'^(?P<member_id>\d+)/$', member.detail),
    url(r'^(?P<member_id>\d+)/signins/$', member.signins),
    url(r'^(?P<member_id>\d+)/signins/json/$', member.signins_json),
    url(r'^(?P<member_id>\d+)/transaction/$', member.transactions),
    url(r'^(?P<member_id>\d+)/bill/$', member.bills),
    url(r'^(?P<member_id>\d+)/membership/$', member.membership),
    url(r'^(?P<member_id>\d+)/files/$', member.files),
    url(r'^(?P<username>[^/]+)/edit/$', member.edit),

    url(r'^stats/$', stats.stats),
    url(r'^stats/history/$', stats.history),
    url(r'^stats/monthly/$', stats.monthly),
    url(r'^stats/gender/$', stats.gender),
    url(r'^stats/neighborhood/$', stats.neighborhood),
    url(r'^stats/membership-history/$', stats.membership_history),
    url(r'^stats/membership-days/$', stats.membership_days),
    url(r'^stats/graph/$', stats.graph),

    url(r'^usaepay/m/$', payment.usaepay_members),
    url(r'^usaepay/void/$', payment.usaepay_void),
    url(r'^usaepay/(?P<username>[^/]+)/$', payment.usaepay_user),
    url(r'^charges/t/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', payment.usaepay_transactions),
    url(r'^charges/t/today/$', payment.usaepay_transactions_today),
    url(r'^xero/(?P<username>[^/]+)/$', payment.xero_user),
]

# Copyright 2009 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
