import os
import pytz
from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings
from django.forms.formsets import formset_factory

from monthdelta import MonthDelta, monthmod

from nadine.forms import MembershipForm, MembershipPackageForm, SubForm
from nadine.models.membership import OldMembership, MembershipPlan, ResourceSubscription
from nadine.models.membership import Membership, MembershipPackage, ResourceSubscription, SubscriptionDefault
from nadine.models.profile import MemberNote, SentEmailLog, FileUpload, SpecialDay
from nadine.models.organization import Organization
from nadine.forms import MemberSearchForm, MembershipForm, EventForm
from nadine.utils.slack_api import SlackAPI
from nadine.settings import TIME_ZONE
from nadine.utils import network
from nadine import email

from staff import user_reports

from arpwatch import arp
from arpwatch.models import ArpLog

@staff_member_required
def detail(request, username):
    user = get_object_or_404(User, username=username)
    emergency_contact = user.get_emergency_contact()
    # memberships = OldMembership.objects.filter(user=user).order_by('start_date').reverse()
    # subscriptions = user.membership.first().active_subscriptions()
    # membership = user.
    email_logs = SentEmailLog.objects.filter(user=user).order_by('created').reverse()

    if request.method == 'POST':
        if 'send_manual_email' in request.POST:
            key = request.POST.get('message_key')
            email.send_manual(user, key)
        elif 'add_note' in request.POST:
            note = request.POST.get('note')
            MemberNote.objects.create(user=user, created_by=request.user, note=note)
        elif 'add_special_day' in request.POST:
            month = request.POST.get('month')
            day = request.POST.get('day')
            year = request.POST.get('year')
            if len(year) == 0:
                year = None
            desc = request.POST.get('description')
            SpecialDay.objects.create(user=user, month=month, day=day, year=year, description=desc)
        else:
            print(request.POST)

    staff_members = User.objects.filter(is_staff=True).order_by('id').reverse()
    email_keys = email.valid_message_keys()
    email_keys.remove("all")

    context = {
        'user': user,
        'emergency_contact': emergency_contact,
        'email_logs': email_logs,
        'email_keys': email_keys,
        'staff_members':staff_members,
        'settings': settings,
    }
    return render(request, 'staff/user/detail.html', context)


@staff_member_required
def members(request, group=None):
    if not group:
        first_package = MembershipPackage.objects.filter(enabled=True).order_by('name').first()
        if first_package:
            group = first_package.name

    users = MemberGroups.get_members(group)
    if users:
        member_count = users.count()
        group_name = MemberGroups.GROUP_DICT[group]
    else:
        # Assume the group is a membership plan
        users = User.helper.members_by_package(group)
        member_count = len(users)
        group_name = "%s Members" % group

    # How many members do we have?
    total_members = User.helper.active_members().count()
    group_list = MemberGroups.get_member_groups()

    context = {
        'group': group,
        'group_name': group_name,
        'users': users,
        'member_count': member_count,
        'group_list': group_list,
        'total_members': total_members
    }
    return render(request, 'staff/user/members.html', context)


@staff_member_required
def org_list(request):
    orgs = Organization.objects.active_organizations().order_by('name')
    context = {
        'organizations': orgs,
    }
    return render(request, 'staff/user/org_list.html', context)


@staff_member_required
def org_view(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    context = {
        'organization': org,
    }
    return render(request, 'staff/user/org_view.html', context)


def bcc_tool(request, group=None):
    if not group:
        group = MemberGroups.ALL
        group_name = "All Members"
        users = User.helper.active_members()
    elif group in MemberGroups.GROUP_DICT:
        group_name = MemberGroups.GROUP_DICT[group]
        users = MemberGroups.get_members(group)
    else:
        group_name = "%s Members" % group
        users = User.helper.members_by_package(group)
    group_list = MemberGroups.get_member_groups()
    context = {'group': group, 'group_name': group_name, 'group_list': group_list, 'users': users}
    return render(request, 'staff/user/bcc_tool.html', context)


@staff_member_required
def export_users(request):
    if 'active_only' in request.GET:
        users = User.helper.active_members()
    else:
        users = User.objects.all()
    context = {'member_list': users}
    return render(request, 'staff/user/memberList.csv', context)


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
            return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))

    active_deposits = []
    inactive_deposits = []
    total_deposits = 0
    for deposit in SecurityDeposit.objects.filter(returned_date=None).order_by('user__username'):
        d = {'username': deposit.user.username,
             'name': deposit.user.get_full_name(),
             'deposit_id': deposit.id,
             'amount': deposit.amount}
        if deposit.user.profile.is_active():
            active_deposits.append(d)
        else:
            inactive_deposits.append(d)
        total_deposits = total_deposits + deposit.amount
    context = {'active_deposits': active_deposits,
               'inactive_deposits': inactive_deposits,
               'total_deposits': total_deposits
               }
    return render(request, 'staff/user/security_deposits.html', context)


@staff_member_required
def member_search(request):
    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            term = member_search_form.cleaned_data['terms']
            search_results = User.helper.search(term)
            if len(search_results) == 1:
                return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': search_results[0].username}))
    else:
        member_search_form = MemberSearchForm()
    context = {'member_search_form': member_search_form, 'search_results': search_results, 'term': term, }
    return render(request, 'staff/user/search.html', context)




@staff_member_required
def view_user_reports(request):
    if request.method == 'POST':
        form = user_reports.UserReportForm(request.POST, request.FILES)
    else:
        form = user_reports.getDefaultForm()

    report = user_reports.User_Report(form)
    users = report.get_users()
    return render(request, 'staff/user/user_reports.html', {'users': users, 'form': form})


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
    return render(request, 'staff/user/slack_users.html', context)


@staff_member_required
def files(request, username):
    user = get_object_or_404(User, username=username)

    if 'delete' in request.POST:
        upload_obj = get_object_or_404(FileUpload, pk=request.POST['file_id'])
        if os.path.exists(upload_obj.file.path):
            os.remove(upload_obj.file.path)
        upload_obj.delete()
    if 'file' in request.FILES:
        try:
            upload = request.FILES['file']
            file_user = User.objects.get(username=request.POST['user'])
            doc_type = request.POST['doc_type']
            FileUpload.objects.create_from_file(file_user, upload, doc_type, request.user)
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not upload file: (%s)" % e)

    doc_types = FileUpload.DOC_TYPES
    files = FileUpload.objects.filter(user=user)

    context = {'user':user, 'files': files, 'doc_types': doc_types}
    return render(request, 'staff/user/files.html', context)


@staff_member_required
def membership(request, username):
    user = get_object_or_404(User, username=username)
    subscriptions = None
    sub_data = None
    start = None
    active_members = User.helper.active_members()
    SubFormSet = formset_factory(SubForm)
    package = request.GET.get('package', None)
    bill_day = request.GET.get('bill_day', user.membership.bill_day)

    if package:
        subscriptions = SubscriptionDefault.objects.filter(package=package)
        sub_data=[{'resource': s.resource, 'allowance':s.allowance, 'start_date':timezone.now().date(), 'end_date': None, 'username': user.username, 'created_by': request.user, 'monthly_rate': s.monthly_rate, 'overage_rate': s.overage_rate, 'paid_by': None} for s in subscriptions]

    if request.method == 'POST':
        if 'ending' in request.POST:
            if request.POST['ending'] == 'today':
                end_target = datetime.now(pytz.timezone(TIME_ZONE)).date()
                user.membership.end_all(end_target)
            elif request.POST['ending'] == 'eop':
                user.membership.end_at_period_end()
            else:
                end_target = request.POST['date-end']
                user.membership.end_all(end_target)
            return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))
        elif 'update' in request.POST:
            s_id = request.POST['id']
            s = ResourceSubscription.objects.get(id=s_id)
            s.allowance = request.POST['allowance']
            s.start_date = request.POST['start_date']
            if request.POST['end_date']:
                s.end_date = request.POST['end_date']
            s.monthly_rate = request.POST.get('monthly_rate', 0)
            s.overage_rate = request.POST.get('overage_rate', 0)
            if request.POST['paid_by'] != 'None':
                paid_by_username = request.POST['paid_by']
                s.paid_by = User.objects.get(username=paid_by_username)
            s.save()
            return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))
        elif 'add' in request.POST:
            add_form = SubForm(request.POST)
            if add_form.is_valid():
                add_form.save()
                return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))
        else:
            package_form = MembershipPackageForm(request.POST)
            sub_formset = SubFormSet(request.POST)
            if sub_formset.is_valid():
                try:
                    with transaction.atomic():
                        new_subs = []
                        membership = package_form.save()
                        for sub_form in sub_formset:
                            paid_by = None
                            resource = sub_form.cleaned_data.get('resource', None)
                            allowance = sub_form.cleaned_data.get('allowance', None)
                            start_date = sub_form.cleaned_data.get('start_date', None)
                            if start_date:
                                start = start_date
                            end_date = sub_form.cleaned_data.get('end_date', None)
                            monthly_rate = sub_form.cleaned_data.get('monthly_rate', None)
                            overage_rate = sub_form.cleaned_data.get('overage_rate', None)
                            paid_by_username = sub_form.cleaned_data.get('paid_by', None)
                            if paid_by_username:
                                paid_by = User.objects.get(username=paid_by_username)

                            if resource and start_date:
                                new_subs.append(ResourceSubscription(created_ts=timezone.now(), created_by=request.user, resource=resource, allowance=allowance, start_date=start_date, end_date=end_date, monthly_rate=monthly_rate, overage_rate=overage_rate, paid_by=paid_by, membership=membership))
                        end_target = start - timedelta(days=1)
                        user.membership.end_all(end_target)
                        ResourceSubscription.objects.bulk_create(new_subs)
                        messages.success(request, "You have updated the subscriptions")
                        return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))

                except IntegrityError:
                    messages.error(request, 'There was an error updating the subscriptions')
            else:
                print sub_formset.errors
    else:
        package_form = MembershipPackageForm()
        sub_formset = SubFormSet(initial=sub_data)
        add_form = SubForm()
    context = {
        'entity': user,
        'subscriptions':subscriptions,
        'package_form': package_form,
        'add_form': add_form,
        'package': package,
        'bill_day': bill_day,
        'sub_formset': sub_formset,
        'active_members': active_members,
    }
    return render(request, 'staff/user/membership.html', context)


################################################################################
# TODO - deprecated
################################################################################


@staff_member_required
def old_add_membership(request, username):
    user = get_object_or_404(User, username=username)

    start = today = timezone.localtime(timezone.now()).date()
    last_membership = user.profile.last_membership()
    if last_membership and last_membership.end_date and last_membership.end_date > today - timedelta(days=10):
        start = (last_membership.end_date + timedelta(days=1))
    last = start + MonthDelta(1) - timedelta(days=1)

    if request.method == 'POST':
      membership_form = MembershipForm(request.POST, request.FILES)
      try:
          if membership_form.is_valid():
              membership_form.created_by = request.user
              membership_form.save()
              return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': username}))
      except Exception as e:
          messages.add_message(request, messages.ERROR, e)
    else:
      membership_form = MembershipForm(initial={'username': username, 'start_date': start})

    # Send them to the update page if we don't have an end date
    if (last_membership and not last_membership.end_date):
      return HttpResponseRedirect(reverse('staff:user:membership', kwargs={'membership_id': last_membership.id}))

    plans = MembershipPlan.objects.filter(enabled=True).order_by('name')
    context = {'user':user, 'membership_plans': plans,
      'membership_form': membership_form, 'today': today.isoformat(),
      'last': last.isoformat()}
    return render(request, 'staff/user/old_membership.html', context)


@staff_member_required
def old_membership(request, membership_id):
    membership = get_object_or_404(Membership, pk=membership_id)

    if request.method == 'POST':
        membership_form = MembershipForm(request.POST, request.FILES)
        try:
            if membership_form.is_valid():
                membership_form.save()
                return HttpResponseRedirect(reverse('staff:user:detail', kwargs={'username': membership.user.username}))
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
    return render(request, 'staff/user/old_membership.html', context)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
