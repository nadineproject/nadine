import os
import traceback
import operator

from datetime import date, datetime, timedelta

from django.utils import timezone
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
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
#from decimal import Decimal

from nadine.models.core import Member, Membership, MembershipPlan, MemberGroups, SecurityDeposit
from nadine.models.alerts import MemberAlert
from nadine.utils.slack_api import SlackAPI

from staff import user_reports
from staff.forms import MemberSearchForm, MembershipForm

from arpwatch import arp
from arpwatch.models import ArpLog


@staff_member_required
def members(request, group=None):
    if not group:
        first_plan = MembershipPlan.objects.all().order_by('name').first()
        if first_plan:
            group = first_plan.name

    members = MemberGroups.get_members(group)
    if members:
        member_count = members.count()
        group_name = MemberGroups.GROUP_DICT[group]
    else:
        # Assume the group is a membership plan
        members = Member.objects.members_by_plan(group)
        member_count = len(members)
        group_name = "%s Members" % group

    # How many members do we have?
    total_members = Member.objects.active_members().count()
    group_list = MemberGroups.get_member_groups()

    return render_to_response('staff/members.html', {'group': group, 'group_name': group_name, 'members': members,
                                                     'member_count': member_count, 'group_list': group_list, 'total_members': total_members
                                                     }, context_instance=RequestContext(request)
                              )


def member_bcc(request, group=None):
    if not group:
        group = MemberGroups.ALL
        group_name = "All Members"
        members = Member.objects.active_members()
    elif group in MemberGroups.GROUP_DICT:
        group_name = MemberGroups.GROUP_DICT[group]
        members = MemberGroups.get_members(group)
    else:
        group_name = "%s Members" % group
        members = Member.objects.members_by_plan(group)
    group_list = MemberGroups.get_member_groups()
    print group
    return render_to_response('staff/member_bcc.html', {'group': group, 'group_name': group_name, 'group_list': group_list, 'members': members}, context_instance=RequestContext(request))


@staff_member_required
def export_members(request):
    if 'active_only' in request.GET:
        members = Member.objects.active_members()
    else:
        members = Member.objects.all()
    return render_to_response('staff/memberList.csv', {'member_list': members}, content_type="text/plain")


@staff_member_required
def security_deposits(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        today = timezone.localtime(timezone.now())
        if 'mark_returned' in request.POST:
            deposit = SecurityDeposit.objects.get(pk=request.POST.get('deposit_id'))
            deposit.returned_date = today
            deposit.save()
        elif 'add_deposit' in request.POST:
            member = Member.objects.get(pk=member_id)
            amount = request.POST.get('amount')
            note = request.POST.get('note')
            deposit = SecurityDeposit.objects.create(member=member, received_date=today, amount=amount, note=note)
            deposit.save()
        if member_id:
            return HttpResponseRedirect(reverse('staff.views.member.detail', args=[], kwargs={'member_id': member_id}))

    members = []
    total_deposits = 0
    for deposit in SecurityDeposit.objects.filter(returned_date=None).order_by('member'):
        members.append({'id': deposit.member.id, 'name': deposit.member, 'deposit_id': deposit.id, 'deposit': deposit.amount})
        total_deposits = total_deposits + deposit.amount
    return render_to_response('staff/security_deposits.html', {'member_list': members, 'total_deposits': total_deposits}, context_instance=RequestContext(request))


@staff_member_required
def member_search(request):
    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            search_results = Member.objects.search(member_search_form.cleaned_data['terms'])
            if len(search_results) == 1:
                return HttpResponseRedirect(reverse('staff.views.member.detail', args=[], kwargs={'member_id': search_results[0].id}))
    else:
        member_search_form = MemberSearchForm()
    return render_to_response('staff/member_search.html', {'member_search_form': member_search_form, 'search_results': search_results}, context_instance=RequestContext(request))


@staff_member_required
def todo(request):
    member_alerts = []
    for key, desc in MemberAlert.ALERT_DESCRIPTIONS:
        count = MemberAlert.objects.unresolved(key).count()
        member_alerts.append((key, desc, count))

    showall = "showall" in request.GET

    # Did anyone forget to sign in in the last 7 days?
    check_date = timezone.now().date() - timedelta(days=7)
    not_signed_in = Member.objects.not_signed_in_since(check_date)
    today = timezone.now().date()

    return render_to_response('staff/todo.html', {'member_alerts': member_alerts, 'not_signed_in': not_signed_in, 'showall':showall, 'today':today}, context_instance=RequestContext(request))


@staff_member_required
def todo_detail(request, key):
    if request.method == 'POST' and "action" in request.POST:
        action = request.POST.get("action").lower()
        try:
            alert = get_object_or_404(MemberAlert, pk=request.POST.get("alert_id"))
            note = None
            if "note" in request.POST:
                note = request.POST.get("note").strip()
            if action == "resolve":
                alert.resolve(request.user, note=note)
                messages.add_message(request, messages.INFO, "Alert '%s:%s' resolved!" % (alert.user.username, alert.key))
            elif action == "mute":
                if note:
                    alert.mute(request.user, note=note)
                    messages.add_message(request, messages.INFO, "Alert '%s:%s' muted!" % (alert.user.username, alert.key))
                else:
                    messages.add_message(request, messages.ERROR, "Note required to mute an alert!")
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not %s alert: %s" % (action, e))
        if "next" in request.POST:
            next_url = request.POST.get("next")
            return HttpResponseRedirect(next_url)


    alerts = MemberAlert.objects.unresolved(key).order_by('user__first_name')
    description = MemberAlert.getDescription(key)
    is_system_alert = MemberAlert.isSystemAlert(key)

    return render_to_response('staff/todo_detail.html', {'key': key, 'description': description, 'alerts': alerts,
            'is_system_alert': is_system_alert}, context_instance=RequestContext(request))


@staff_member_required
def membership(request, membership_id):
    membership = get_object_or_404(Membership, pk=membership_id)

    if request.method == 'POST':
        membership_form = MembershipForm(request.POST, request.FILES)
        try:
            if membership_form.is_valid():
                membership_form.save()
                return HttpResponseRedirect(reverse('staff.views.member.detail', args=[], kwargs={'member_id': membership.member.id}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)
    else:
        membership_form = MembershipForm(initial={'membership_id': membership.id, 'member': membership.member.id, 'membership_plan': membership.membership_plan,
                                                  'start_date': membership.start_date, 'end_date': membership.end_date, 'monthly_rate': membership.monthly_rate, 'dropin_allowance': membership.dropin_allowance,
                                                  'daily_rate': membership.daily_rate, 'has_desk': membership.has_desk, 'has_key': membership.has_key, 'has_mail': membership.has_mail,
                                                  'guest_of': membership.guest_of})

    today = timezone.localtime(timezone.now()).date()
    last = membership.next_billing_date() - timedelta(days=1)
    return render_to_response('staff/membership.html', {'member': membership.member, 'membership': membership, 'membership_plans': MembershipPlan.objects.all(),
                                                        'membership_form': membership_form, 'today': today.isoformat(), 'last': last.isoformat()}, context_instance=RequestContext(request))


@staff_member_required
def view_user_reports(request):
    if request.method == 'POST':
        form = user_reports.UserReportForm(request.POST, request.FILES)
    else:
        form = user_reports.getDefaultForm()

    report = user_reports.User_Report(form)
    users = report.get_users()
    return render_to_response('staff/user_reports.html', {'users': users, 'form': form}, context_instance=RequestContext(request))



@staff_member_required
def slack_users(request):
    expired_users = Member.objects.expired_slack_users()
    slack_emails = []
    slack_users = SlackAPI().users.list().body['members']
    for u in slack_users:
        if 'profile' in u and 'email' in u['profile'] and u['profile']['email']:
            slack_emails.append(u['profile']['email'])
    non_slack_users = Member.objects.active_members().exclude(user__email__in=slack_emails)
    return render_to_response('staff/slack_users.html', {'expired_users':expired_users,
                                                         'slack_users':slack_users,
                                                         'non_slack_users':non_slack_users,
                                                         'slack_url':settings.SLACK_TEAM_URL}, context_instance=RequestContext(request))

def view_ip(request):
    ip = None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return render_to_response('staff/ip.html', {'ip': ip}, context_instance=RequestContext(request))
