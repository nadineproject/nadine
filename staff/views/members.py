import os
import ast
import unicodedata
from datetime import date, datetime, timedelta
from collections import namedtuple
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.forms.formsets import formset_factory
from django.urls import reverse
from django.contrib import messages
from django.utils.timezone import localtime, now

from nadine.forms import MembershipForm, SubscriptionForm, MemberSearchForm, EventForm, NewUserForm
from nadine.models.membership import MemberGroups, Membership, MembershipPackage, ResourceSubscription, SubscriptionDefault, SecurityDeposit
from nadine.models.billing import UserBill
from nadine.models.profile import MemberNote, SentEmailLog, FileUpload, SpecialDay
from nadine.models.resource import Resource
from nadine.models.organization import Organization
from nadine.utils.slack_api import SlackAPI
from nadine.utils.payment_api import PaymentAPI
from nadine.settings import TIME_ZONE, DEFAULT_BILLING_DAY
from nadine.utils import network
from nadine import email

from staff import user_reports

from arpwatch import arp
from arpwatch.models import ArpLog


@staff_member_required
def detail(request, username):
    user = get_object_or_404(User, username=username)
    membership = Membership.objects.for_user(user)
    active_subscriptions = membership.subscriptions_for_day(target_date=localtime(now()).date())
    emergency_contact = user.get_emergency_contact()
    email_logs = SentEmailLog.objects.filter(user=user).order_by('created').reverse()
    member_notes = user.get_member_notes()
    payer = None
    payer_url = None
    for s in membership.active_subscriptions():
        if s.paid_by:
            payer = s.paid_by

    if request.method == 'POST':
        if 'send_manual_email' in request.POST:
            key = request.POST.get('message_key')
            email.send_manual(user, key)
        elif 'add_note' in request.POST:
            note = request.POST.get('note')
            print(note)
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
            print((request.POST))
    staff_members = User.objects.filter(is_staff=True).order_by('id').reverse()
    email_keys = email.valid_message_keys()
    email_keys.remove("all")

    context = {
        'user': user,
        'emergency_contact': emergency_contact,
        'active_subscriptions': active_subscriptions,
        'email_logs': email_logs,
        'email_keys': email_keys,
        'staff_members':staff_members,
        'settings': settings,
        'member_notes': member_notes,
        'payer': payer,
    }
    return render(request, 'staff/members/detail.html', context)


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
        group_name = "%s Members" % group
        member_count = 0

        # See if our 'group' is a package name
        package = MembershipPackage.objects.filter(name=group).first()
        if package:
            users = User.helper.members_by_package(package.name).order_by('first_name')
            member_count = len(users)

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
    return render(request, 'staff/members/members.html', context)


@staff_member_required
def org_list(request):
    orgs = Organization.objects.active_organizations().order_by('name')
    context = {
        'organizations': orgs,
    }
    return render(request, 'staff/members/org_list.html', context)


@staff_member_required
def org_view(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    context = {
        'organization': org,
    }
    return render(request, 'staff/members/org_view.html', context)


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
    return render(request, 'staff/members/bcc_tool.html', context)


@staff_member_required
def new_user(request):
    # First process our form
    if request.method == "POST":
        form = NewUserForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                messages.success(request, "User: '%s' created." % user.username)
                return HttpResponseRedirect(reverse('staff:members:new_user'))
        except Exception as e:
            messages.error(request, str(e))
    else:
        form = NewUserForm()

    # Grab all the new users in the past X days
    today = localtime(now())
    days_back = 30
    if 'days_back' in request.GET:
        days_back = int(request.GET.get('days_back'))
    new_users = User.objects.filter(date_joined__range=(today - timedelta(days=days_back), today)).order_by('-date_joined')

    context = {
        'new_user_form': form,
        'new_users': new_users,
        'days_back': days_back,
    }
    return render(request, 'staff/members/new_user.html', context)


@staff_member_required
def export_users(request):
    if 'active_only' in request.GET:
        users = User.helper.active_members()
    else:
        users = User.objects.all()
    context = {'member_list': users}
    return render(request, 'staff/members/memberList.csv', context)


@staff_member_required
def security_deposits(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        today = localtime(now())
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
            return HttpResponseRedirect(reverse('staff:members:detail', kwargs={'username': username}))

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
    return render(request, 'staff/members/security_deposits.html', context)


@staff_member_required
def member_search(request):
    term = None
    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            term = member_search_form.cleaned_data['terms']
            search_results = User.helper.search(term)
            if len(search_results) == 1:
                return HttpResponseRedirect(reverse('staff:members:detail', kwargs={'username': search_results[0].username}))
    else:
        member_search_form = MemberSearchForm()
    context = {'member_search_form': member_search_form, 'search_results': search_results, 'term': term, }
    return render(request, 'staff/members/search.html', context)


@staff_member_required
def view_user_reports(request):
    if request.method == 'POST':
        form = user_reports.UserReportForm(request.POST, request.FILES)
    else:
        form = user_reports.getDefaultForm()

    report = user_reports.User_Report(form)
    users = report.get_users()
    return render(request, 'staff/members/user_reports.html', {'users': users, 'form': form})


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
    return render(request, 'staff/members/slack_users.html', context)


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
    return render(request, 'staff/members/files.html', context)


@staff_member_required
def membership(request, username):
    user = get_object_or_404(User, username=username)
    membership = Membership.objects.for_user(user)
    subscriptions = None
    sub_data = None
    start = None
    action = request.GET.get('action', None)
    active_members = User.helper.active_members()
    active_billing = User.objects.filter(profile__valid_billing=True).order_by('first_name')
    SubFormSet = formset_factory(SubscriptionForm)
    old_pkg = None
    bill_day = membership.bill_day

    if membership.package_name and membership.active_subscriptions():
        old_pkg_name = membership.package_name()
        old_pkg = MembershipPackage.objects.get(name=old_pkg_name).id
    package = request.GET.get('package', old_pkg)
    today = localtime(now()).date()
    target_date = request.GET.get('target_date', None)

    if package != old_pkg:
        subscriptions = SubscriptionDefault.objects.filter(package=package)
        sub_data=[{'s_id': None, 'resource': s.resource, 'allowance':s.allowance, 'start_date': today, 'end_date': None, 'username': user.username, 'created_by': request.user, 'monthly_rate': s.monthly_rate, 'overage_rate': s.overage_rate, 'paid_by': None} for s in subscriptions]
        action = 'change'
    else:
        subscriptions = membership.active_subscriptions()
        sub_data=[{'s_id': s.id, 'package_name': s.package_name, 'resource': s.resource, 'allowance':s.allowance, 'start_date':s.start_date, 'end_date': s.end_date, 'username': user.username, 'created_by': s.created_by, 'monthly_rate': s.monthly_rate, 'overage_rate': s.overage_rate, 'paid_by': s.paid_by} for s in subscriptions]


    if request.method == 'POST':
        if 'ending' in request.POST:
            if request.POST['ending'] == 'today':
                end_date = today
                end_target = end_date.strftime('%Y-%m-%d')
            elif request.POST['ending'] == 'yesterday':
                end_date = today - timedelta(days=1)
                end_target = end_date.strftime('%Y-%m-%d')
            elif request.POST['ending'] == 'eop':
                ps, end_date = user.membership.get_period()
                end_target = end_date.strftime('%Y-%m-%d')
            else:
                end_target = request.POST['date-end']

            return HttpResponseRedirect(reverse('staff:members:confirm', kwargs={'username': username, 'package': None, 'new_subs': None, 'end_target': end_target, 'start_target': None}))
        else:
            package_form = MembershipForm(request.POST)
            sub_formset = SubFormSet(request.POST)
            if sub_formset.is_valid() and package_form.is_valid():
                try:
                    with transaction.atomic():
                        new_subs = []
                        package = request.POST['package']
                        membership = {'package': package}
                        for sub_form in sub_formset:
                            paid_by = None
                            package_name = MembershipPackage.objects.get(id=package).name
                            s_id = sub_form.cleaned_data.get('s_id', None)
                            resource = sub_form.cleaned_data.get('resource', None)
                            allowance = sub_form.cleaned_data.get('allowance', None)
                            start_date = sub_form.cleaned_data.get('start_date', None)
                            if start_date:
                                start = start_date
                                start_date = start_date.strftime('%Y-%m-%d')
                            end_date = sub_form.cleaned_data.get('end_date', None)
                            if end_date:
                                end_date = end_date.strftime('%Y-%m-%d')
                            monthly_rate = sub_form.cleaned_data.get('monthly_rate', None)
                            overage_rate = sub_form.cleaned_data.get('overage_rate', None)
                            paid_by = sub_form.cleaned_data.get('paid_by', None)
                            if resource and start_date:
                                new_subs.append({'s_id': s_id, 'resource':resource.id,
                                'package_name': package_name, 'allowance':allowance, 'start_date':start_date, 'end_date':end_date, 'monthly_rate': monthly_rate, 'overage_rate':overage_rate, 'paid_by':paid_by, 'membership':None})
                        end_target = start - timedelta(days=1)
                        return HttpResponseRedirect(reverse('staff:members:confirm', kwargs={'username': username, 'package': membership, 'end_target': end_target, 'start_target': start, 'new_subs': new_subs}))

                except IntegrityError:
                    messages.error(request, 'There was an error updating the subscriptions')
            else:
                print((sub_formset.errors))
                print((package_form.errors))
                messages.error(request, 'There was an error updating the subscriptions')
    else:
        package_form = MembershipForm()
        sub_formset = SubFormSet(initial=sub_data)
    context = {
        'entity': user,
        'subscriptions':subscriptions,
        'package_form': package_form,
        'package': package,
        'sub_formset': sub_formset,
        'active_members': active_members,
        'active_billing': active_billing,
        'target_date': target_date,
        'bill_day': bill_day,
        'action': action,
    }
    return render(request, 'staff/members/membership.html', context)

@staff_member_required
def confirm_membership(request, username, package, end_target, start_target, new_subs):
    user = get_object_or_404(User, username=username)
    membership = Membership.objects.for_user(user)
    subs = ast.literal_eval(new_subs)
    matches_package = user.membership.matching_package(subscriptions=subs)
    pkg = ast.literal_eval(package)
    match = None
    old_pkg = None
    if start_target != 'None':
        activity_target = datetime.strptime(start_target, '%Y-%m-%d')

    if user.membership.package_name():
        old_pkg = MembershipPackage.objects.get(name=user.membership.package_name())

    if len(membership.active_subscriptions(datetime.strptime(end_target, '%Y-%m-%d'))):
        ending_pkg = True
    else:
        ending_pkg = False

    if pkg:
        pkg_name = MembershipPackage.objects.get(id=pkg['package']).name
        if matches_package and matches_package.name != pkg_name:
            match = matches_package
    else:
        pkg_name = None

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Check to see if new membership package. If so, end all previous subscriptions
                membership = Membership.objects.for_user(user)
                if pkg:
                    # If there is a package, then make changes, else, we are ending all
                    if request.POST.get('match'):
                        pkg_name = MembershipPackage.objects.get(id=request.POST.get('match')).name
                    if len(membership.active_subscriptions()) == 0:
                        if settings.DEFAULT_BILLING_DAY == 0:
                            if membership.subscriptions_for_day(activity_target).count() == 0:
                                membership.change_bill_day(activity_target)
                        else:
                            membership.bill_day = settings.DEFAULT_BILLING_DAY
                            membership.save()

                    if user.membership.package_name() != pkg_name:
                        for s in user.membership.active_subscriptions():
                            if s.end_date == None:
                                s.end_date = end_target
                                s.save()
                        """When a membership is created, add the user to any opt-out mailing lists"""

                    # Review all subscriptions to see if adding or ending
                    for sub in subs:
                        sub_id = sub['s_id']
                        if sub_id != None:
                            if sub_id and sub['end_date']:
                                to_end = ResourceSubscription.objects.get(id=sub_id)
                                if to_end.end_date == None:
                                    end_date = sub['end_date']
                                    to_end.end_date = sub['end_date']
                                    to_end.save()
                                    slack = None
                        else:
                            """ If not ending then create subscriptions """
                            paid_by = None
                            created_ts = localtime(now())
                            created_by = request.user
                            resource = Resource.objects.get(id=sub['resource'])
                            allowance = sub['allowance']
                            start_date = sub['start_date']
                            starting_bill_day = start_date
                            package_name = pkg_name
                            if sub['end_date']:
                                end_date = sub['end_date']
                            else:
                                end_date = None
                            monthly_rate = sub['monthly_rate']
                            overage_rate = sub['overage_rate']
                            if sub['paid_by']:
                                p_username = sub['paid_by']
                                paid_by = User.objects.get(username=p_username)

                            """ Check to see if it is a unique resource and end if it is not """
                            already_have = membership.active_subscriptions().filter(resource=resource).filter(paid_by=paid_by)
                            if len(already_have) > 0:
                                p_id = already_have[0].id
                                prev_rs = ResourceSubscription.objects.get(id=p_id)
                                if not prev_rs.end_date:
                                    allowance = int(allowance) + prev_rs.allowance
                                    monthly_rate = int(monthly_rate) + prev_rs.monthly_rate
                                    prev_rs.end_date = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)
                                    prev_rs.save()
                            # Save new resource
                            rs = ResourceSubscription(created_by=created_by, created_ts=created_ts, package_name=package_name, resource=resource, allowance=allowance, start_date=start_date, end_date=end_date, monthly_rate=monthly_rate, overage_rate=overage_rate, paid_by=paid_by, membership=membership)
                            rs.save()
                else:
                    arr = []
                    for a in user.membership.active_subscriptions():
                        arr.append(a.end_date)
                    if arr.count(arr[0]) == len(arr):
                        user.membership.end_all(end_target)
                    else:
                        for a in user.membership.active_subscriptions():
                            if a.end_date == None:
                                a.end_date = end_target
                                a.save()
                messages.success(request, "You have updated the subscriptions for %s" % username)
                return HttpResponseRedirect(reverse('staff:members:detail', kwargs={'username': username}) + '#tabs-1')
        except IntegrityError as e:
            print(('There was an ERROR: %s' % e.message))
            messages.error(request, 'There was an error setting new membership package')
    context = {
        'user': user,
        'package': pkg,
        'package_name': pkg_name,
        'old_pkg': old_pkg,
        'new_subs': subs,
        'end_target': end_target,
        'match': match,
        'ending_pkg': ending_pkg,
    }
    return render(request, 'staff/members/confirm.html', context)


@staff_member_required
def edit_bill_day(request, username):
    user = get_object_or_404(User, username=username)
    membership = Membership.objects.for_user(user)
    today = localtime(now()).date()
    ps, pe = membership.get_period(target_date=today)

    # Process the change if we recived a date
    if request.method == 'POST' and 'bill-date' in request.POST:
        new_date = datetime.strptime(request.POST.get('bill-date'), '%Y-%m-%d')
        membership.change_bill_day(new_date)
        messages.success(request, 'Updated bill day for %s' % user)
        return HttpResponseRedirect(reverse('staff:members:detail', kwargs={'username': username}) + '#tabs-1')

    # Find an end date on the last closed bill
    end_date = None
    if UserBill.objects.filter(user=user):
        last_bill = UserBill.objects.filter(user=user).filter(closed_ts__isnull=False).order_by('-due_date').last()
        if last_bill:
            end_date = last_bill.due_date.day

    # Look for an open bill in the period we're in
    open_bill = user.bills.get_open_bill(user=user, period_start=ps, period_end=pe)

    context = {
        'user': user,
        'open_bill': open_bill,
        'period_end': end_date,
    }
    return render(request, 'staff/members/edit_bill_day.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
