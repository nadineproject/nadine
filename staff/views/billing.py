import time as timeo
from datetime import date, datetime, timedelta
from collections import OrderedDict

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q, Sum
from django.conf import settings

from decimal import Decimal

from nadine.models import *
from nadine import email
from nadine.forms import PayBillsForm, DateRangeForm
from staff.views.activity import date_range_from_request, START_DATE_PARAM, END_DATE_PARAM


@staff_member_required
def billing_today(request):
    today = localtime(now())
    return HttpResponseRedirect(reverse('staff:billing:daily_billing', args=[], kwargs={'year': today.year, 'month': today.month, 'day': today.day}))


@staff_member_required
def daily_billing(request, year, month, day):
    d = date(year=int(year), month=int(month), day=int(day))
    memberships = []
    for m in Membership.objects.ready_for_billing(target_date=d):
        memberships.append({
            'membership': m,
            'monthly_rate': m.monthly_rate(target_date=d),
            'matching_package': m.matching_package(target_date=d),
            'bills': m.bills_for_period(target_date=d),
            'bill_totals': m.bill_totals(target_date=d),
            'payment_totals': m.payment_totals(target_date=d),
        })
    context = {
        'memberships': memberships,
        'date': d,
        'previous_date': d - timedelta(days=1),
        'next_date': d + timedelta(days=1),
    }
    return render(request, 'staff/billing/daily_billing.html', context)


def group_bills_by_date(bill_query):
    bills_by_date = {}
    for bill in bill_query:
        key = bill.created_ts.date()
        if not key in bills_by_date:
            bills_by_date[key] = []
        bills_by_date[key].append(bill.user)
    # Return an ordered dictionary by date
    ordered_bills = OrderedDict(sorted(bills_by_date.items(), key=lambda t: t[0]))
    return ordered_bills


@staff_member_required
def outstanding(request):
    if request.method == 'POST':
        action = request.POST.get("action", "Set Paid")
        pay_bills_form = PayBillsForm(request.POST)
        if pay_bills_form.is_valid():
            user = User.objects.get(username=pay_bills_form.cleaned_data['username'])
            users_bills = {}
            for bill in user.profile.outstanding_bills():
                users_bills[bill.id] = bill
            bill_ids = [int(bill_id) for bill_id in request.POST.getlist('bill_id')]
            if action == "set_paid":
                amount = pay_bills_form.cleaned_data['amount']
                transaction = Transaction(user=user, status='closed', amount=Decimal(amount))
                transaction.note = pay_bills_form.cleaned_data['transaction_note']
                transaction.save()
                for bill_id in bill_ids:
                    transaction.bills.add(users_bills[bill_id])
                transaction_url = reverse('staff:billing:transaction', args=[], kwargs={'id': transaction.id})
                messages.success(request, 'Created a <a href="%s">transaction for %s</a>' % (transaction_url, user.get_full_name()))
            elif action == "mark_in_progress":
                for bill_id in bill_ids:
                    bill = users_bills[bill_id]
                    bill.in_progress = True
                    bill.save()
                    messages.success(request, "Bills marked 'In Progress'")
            elif action == "clear_in_progress":
                for bill_id in bill_ids:
                    bill = users_bills[bill_id]
                    bill.in_progress = False
                    bill.save()
                    messages.success(request, "Bills updated")

    bills = group_bills_by_date(UserBill.objects.unpaid(in_progress=False))
    bills_in_progress = group_bills_by_date(UserBill.objects.unpaid(in_progress=True))
    invalids = User.helper.invalid_billing()

    context = {
        'bills': bills,
        'bills_in_progress': bills_in_progress,
        'invalid_members': invalids,
    }
    return render(request, 'staff/billing/outstanding.html', context)


@staff_member_required
def bills_pay_all(request, username):
    user = get_object_or_404(User, username=username)
    amount = user.profile.open_bills_amount

    # Save all the bills!
    if amount > 0:
        transaction = Transaction(user=user, status='closed', amount=amount)
        transaction.save()
        for bill in user.profile.outstanding_bills():
            transaction.bills.add(bill)

    # Where to next?
    if request.method == 'POST':
        if 'next' in request.POST:
            next_url = request.POST.get("next")
        else:
            next_url = reverse('staff:billing:outstanding')

    return HttpResponseRedirect(next_url)


@staff_member_required
def bill_list(request):
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    starteo = timeo.strptime(start, "%Y-%m-%d")
    start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
    endeo = timeo.strptime(end, "%Y-%m-%d")
    end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
    bills = UserBill.objects.filter(period_start__range=(start_date, end_date)).order_by('period_start').reverse()
    # total_amount = bills.aggregate(s=Sum('amount'))['s']
    total_amount = 100.00
    context = {
        'bills': bills,
        'total_amount': total_amount,
        'date_range_form': date_range_form,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'staff/billing/bill_list.html', context)


@staff_member_required
def toggle_billing_flag(request, username):
    user = get_object_or_404(User, username=username)

    messages.success(request, user.get_full_name() + " billing profile: ")
    if user.profile.valid_billing:
        user.profile.valid_billing = False
        messages.success(request, user.get_full_name() + " billing profile: Invalid")
        try:
            email.send_invalid_billing(user)
        except Exception:
            messages.error(request, "Failed to send invalid billing email to: " + user.email)
    else:
        user.profile.valid_billing = True
        messages.success(request, user.get_full_name() + " billing profile: Valid")
    user.profile.save()


    if 'back' in request.POST:
        return HttpResponseRedirect(request.POST.get('back'))
    return HttpResponseRedirect(reverse('staff:billing:outstanding'))


@staff_member_required
def generate_bill(request, membership_id, year, month, day):
    membership = get_object_or_404(Membership, id=membership_id)
    target_date = date(year=int(year), month=int(month), day=int(day))
    bills = membership.generate_bill(target_date=target_date, created_by=request.user)
    if bills:
        bill_count = len(bills.keys())
        messages.add_message(request, messages.SUCCESS, "%d Bill(s) Generated" % bill_count)
        if bill_count == 1:
            # If there is only one bill, send them to the bill view page
            bill_id = bills[bills.keys()[0]]['bill'].id
            return HttpResponseRedirect(reverse('staff:billing:bill', kwargs={'bill_id': bill_id}))
    else:
        messages.add_message(request, messages.ERROR, "0 Bills Generated")

    # If there are multiple bills or nothing happend, go to the bill list
    return HttpResponseRedirect(reverse('staff:billing:bills'))


@staff_member_required
def bill_view(request, bill_id):
    bill = get_object_or_404(UserBill, id=bill_id)
    if bill.membership:
        bill_user = User.objects.get(membership = bill.membership)
    else:
        bill_user = bill.user
    benefactor = None
    if bill_user != bill.user:
        benefactor = bill_user
    diff = localtime(now()).date() - bill.period_end
    if diff.days < 1:
        diff = None
    line_items = bill.line_items.all().order_by('id')
    context = {
        "bill": bill,
        "line_items": line_items,
        "diff": diff,
        "benefactor": benefactor,
    }
    return render(request, 'staff/billing/bill_view.html', context)


@staff_member_required
def user_bills(request, username):
    user = get_object_or_404(User, username=username)
    bills = user.bills.all().order_by('-due_date')
    return render(request, 'staff/billing/user_bills.html', {'user':user, 'bills':bills})


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
