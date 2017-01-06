import os
import traceback
import operator

from datetime import date, datetime, timedelta

from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib import messages
from django.conf import settings

#from django.core import serializers
#from django.forms.models import model_to_dict
#from django.db.models import Sum

from nadine.models.membership import Membership, MembershipPlan, MemberGroups, SecurityDeposit
from nadine.forms import MemberSearchForm, MembershipForm, EventForm
from nadine.utils.slack_api import SlackAPI
from nadine.utils import network

from staff import user_reports

from arpwatch import arp
from arpwatch.models import ArpLog


@staff_member_required
def members(request, group=None):
    if not group:
        first_plan = MembershipPlan.objects.all().order_by('name').first()
        if first_plan:
            group = first_plan.name

    users = MemberGroups.get_members(group)
    if users:
        member_count = users.count()
        group_name = MemberGroups.GROUP_DICT[group]
    else:
        # Assume the group is a membership plan
        users = User.helper.members_by_plan(group)
        member_count = len(users)
        group_name = "%s Members" % group

    # How many members do we have?
    total_members = User.helper.active_members().count()
    group_list = MemberGroups.get_member_groups()

    context = {'group': group, 'group_name': group_name, 'users': users,
        'member_count': member_count, 'group_list': group_list, 'total_members': total_members}
    return render(request, 'staff/member/members.html', context)


def member_bcc(request, group=None):
    if not group:
        group = MemberGroups.ALL
        group_name = "All Members"
        users = User.helper.active_members()
    elif group in MemberGroups.GROUP_DICT:
        group_name = MemberGroups.GROUP_DICT[group]
        users = MemberGroups.get_members(group)
    else:
        group_name = "%s Members" % group
        users = User.helper.members_by_plan(group)
    group_list = MemberGroups.get_member_groups()
    context = {'group': group, 'group_name': group_name, 'group_list': group_list, 'users': users}
    return render(request, 'staff/member/member_bcc.html', context)


@staff_member_required
def export_users(request):
    if 'active_only' in request.GET:
        users = User.helper.active_members()
    else:
        users = User.objects.all()
    context = {'member_list': users}
    return render(request, 'staff/member/memberList.csv', context)


@staff_member_required
def security_deposits(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        today = timezone.localtime(timezone.now())
        if 'mark_returned' in request.POST:
            deposit = SecurityDeposit.objects.get(pk=request.POST.get('deposit_id'))
            deposit.returned_date = today
            deposit.save()
        elif 'add_deposit' in request.POST:
            user = User.objects.get(username=username)
            amount = request.POST.get('amount')
            note = request.POST.get('note')
            deposit = SecurityDeposit.objects.create(user=user, received_date=today, amount=amount, note=note)
            deposit.save()
        if username:
            return HttpResponseRedirect(reverse('staff:member:detail', kwargs={'username': username}))

    active_deposits = []
    inactive_deposits = []
    total_deposits = 0
    for deposit in SecurityDeposit.objects.filter(returned_date=None).order_by('user__username'):
        d = {'username': deposit.user.username, 'name': deposit.user.get_full_name(), 'deposit_id': deposit.id, 'amount': deposit.amount}
        if deposit.user.profile.is_active():
            active_deposits.append(d)
        else:
            inactive_deposits.append(d)
        total_deposits = total_deposits + deposit.amount
    context = {'active_deposits': active_deposits,
        'inactive_deposits':inactive_deposits,
        'total_deposits': total_deposits
    }
    return render(request, 'staff/member/security_deposits.html', context)


@staff_member_required
def member_search(request):
    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            search_results = User.helper.search(member_search_form.cleaned_data['terms'])
            if len(search_results) == 1:
                return HttpResponseRedirect(reverse('staff:member:detail', kwargs={'username': search_results[0].username}))
    else:
        member_search_form = MemberSearchForm()
    context = {'member_search_form': member_search_form, 'search_results': search_results}
    return render(request, 'staff/member/member_search.html', context)


@staff_member_required
def membership(request, membership_id):
    membership = get_object_or_404(Membership, pk=membership_id)

    if request.method == 'POST':
        membership_form = MembershipForm(request.POST, request.FILES)
        try:
            if membership_form.is_valid():
                membership_form.save()
                return HttpResponseRedirect(reverse('staff:member:detail', kwargs={'username': membership.user.username}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)
    else:
        membership_form = MembershipForm(initial={'membership_id': membership.id, 'username': membership.user.username, 'membership_plan': membership.membership_plan,
                                                  'start_date': membership.start_date, 'end_date': membership.end_date, 'monthly_rate': membership.monthly_rate, 'dropin_allowance': membership.dropin_allowance,
                                                  'daily_rate': membership.daily_rate, 'has_desk': membership.has_desk, 'has_key': membership.has_key, 'has_mail': membership.has_mail,
                                                  'paid_by': membership.paid_by})

    today = timezone.localtime(timezone.now()).date()
    last = membership.next_billing_date() - timedelta(days=1)

    context = {'user': membership.user, 'membership': membership,
        'membership_plans': MembershipPlan.objects.all(), 'membership_form': membership_form,
        'today': today.isoformat(), 'last': last.isoformat()}
    return render(request, 'staff/member/membership.html', context)


@staff_member_required
def view_user_reports(request):
    if request.method == 'POST':
        form = user_reports.UserReportForm(request.POST, request.FILES)
    else:
        form = user_reports.getDefaultForm()

    report = user_reports.User_Report(form)
    users = report.get_users()
    return render(request, 'staff/member/user_reports.html', {'users': users, 'form': form})


@staff_member_required
def slack_users(request):
    expired_users = User.helper.expired_slack_users()
    slack_emails = []
    slack_users = SlackAPI().users.list().body['members']
    for u in slack_users:
        if 'profile' in u and 'email' in u['profile'] and u['profile']['email']:
            slack_emails.append(u['profile']['email'])
    non_slack_users = User.helper.active_members().exclude(email__in=slack_emails)
    context = {'expired_users':expired_users, 'slack_users':slack_users,
         'non_slack_users':non_slack_users, 'slack_url':settings.SLACK_TEAM_URL}
    return render(request, 'staff/member/slack_users.html', context)


@staff_member_required
def view_ip(request):
    ip = network.get_addr(request)
    return render(request, 'staff/view_ip.html', {'ip': ip})


@staff_member_required
def view_config(request):
    return render(request, 'staff/view_config.html', {})


@staff_member_required
# TODO - evaluate
def create_event(request):
    if request.method == 'POST':
        event_form = EventForm(request.POST)
        if event_form.is_valid():
            event_form.save()
            return HttpResponseRedirect(reverse('staff_todo'))
    else:
        event_form = EventForm()
    return render(request, 'staff/create_event.html', {'event_form': event_form})


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
