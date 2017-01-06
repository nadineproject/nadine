import os
from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

from monthdelta import MonthDelta, monthmod

from nadine.forms import MembershipForm
from nadine.models import Membership, MemberNote, MembershipPlan, SentEmailLog, FileUpload, SpecialDay
from nadine import email


@staff_member_required
def detail(request, username):
    user = get_object_or_404(User, username=username)
    emergency_contact = user.get_emergency_contact()
    memberships = Membership.objects.filter(user=user).order_by('start_date').reverse()
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

    context = {'user':user, 'emergency_contact': emergency_contact,
        'memberships': memberships, 'email_logs': email_logs,
        'email_keys': email_keys, 'settings': settings,
        'staff_members':staff_members,
    }
    return render(request, 'staff/member/detail.html', context)


@staff_member_required
def transactions(request, username):
    user = get_object_or_404(User, username=username)
    transactions = user.transaction_set.all()
    return render(request, 'staff/member/transactions.html', {'user':user, 'transactions':transactions})


@staff_member_required
def bills(request, username):
    user = get_object_or_404(User, username=username)
    bills = user.bill_set.all()
    return render(request, 'staff/member/bills.html', {'user':user, 'bills':bills})


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
    return render(request, 'staff/member/files.html', context)


@staff_member_required
def membership(request, username):
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
                return HttpResponseRedirect(reverse('staff:member:detail', kwargs={'username': username}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)
    else:
        membership_form = MembershipForm(initial={'username': username, 'start_date': start})

    # Send them to the update page if we don't have an end date
    if (last_membership and not last_membership.end_date):
        return HttpResponseRedirect(reverse('staff:member:memberships', kwargs={'membership_id': last_membership.id}))

    plans = MembershipPlan.objects.filter(enabled=True).order_by('name')
    context = {'user':user, 'membership_plans': plans,
        'membership_form': membership_form, 'today': today.isoformat(),
        'last': last.isoformat()}
    return render(request, 'staff/member/membership.html', context)


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
