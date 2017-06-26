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
from nadine.forms import PaymentForm, DateRangeForm
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
            'package_name': m.package_name(target_date=d),
            'monthly_rate': m.monthly_rate(target_date=d),
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
def outstanding(request):
    bills = UserBill.objects.outstanding().filter(in_progress=False).order_by('due_date')
    bills_in_progress = UserBill.objects.outstanding().filter(in_progress=True).order_by('due_date')
    invalids = User.helper.invalid_billing()
    context = {
        'bills': bills,
        'bills_in_progress': bills_in_progress,
        'invalid_members': invalids,
    }
    return render(request, 'staff/billing/outstanding.html', context)


@staff_member_required
def action_bill_paid(request, bill_id):
    ''' Mark the bill paid '''
    bill = get_object_or_404(UserBill, id=bill_id)
    payment = Payment.objects.create(bill=bill, user=bill.user, amount=bill.amount, created_by=request.user)
    if 'payment_date' in request.POST:
        payment.created_ts = datetime.strptime(request.POST['payment_date'], "%Y-%m-%d").date()
        payment.save()
    messages.success(request, "Bill %d ($%s) paid" % (bill.id, bill.amount))
    if 'next' in request.POST:
        return HttpResponseRedirect(request.POST['next'])
    return HttpResponseRedirect(reverse('staff:billing:outstanding'))


@staff_member_required
def action_bill_delay(request, bill_id):
    ''' Turn on/off the in_progress flag of this bill '''
    bill = get_object_or_404(UserBill, id=bill_id)
    if bill.in_progress == True:
        bill.in_progress = False
        bill.save()
        messages.success(request, "Bill %s no longer 'in progress'" % bill_id)
    else:
        bill.in_progress = True
        bill.save()
        messages.success(request, "Bill %s now 'in progress'" % bill_id)
    if 'next' in request.POST:
        return HttpResponseRedirect(request.POST.get('next'))
    return HttpResponseRedirect(reverse('staff:billing:outstanding'))


@staff_member_required
def action_billing_flag(request, username):
    ''' Turn on/off the valid_billing flag of this user '''
    user = get_object_or_404(User, username=username)
    if user.profile.valid_billing:
        user.profile.valid_billing = False
        user.profile.save()
        messages.success(request, user.get_full_name() + " billing profile: Invalid")
        try:
            email.send_invalid_billing(user)
        except Exception:
            messages.error(request, "Failed to send invalid billing email to: " + user.email)
    else:
        user.profile.valid_billing = True
        user.profile.save()
        messages.success(request, user.get_full_name() + " billing profile: Valid")
    if 'next' in request.POST:
        return HttpResponseRedirect(request.POST.get('next'))
    return HttpResponseRedirect(reverse('staff:billing:outstanding'))


@staff_member_required
def action_generate_bill(request, membership_id, year=None, month=None, day=None):
    ''' Generate the bills for the given membership and date '''
    membership = get_object_or_404(Membership, id=membership_id)
    if year and month and day:
        target_date = date(year=int(year), month=int(month), day=int(day))
    else:
        target_date = localtime(now()).date()
    bill_count = 0
    bills = membership.generate_bills(target_date=target_date, created_by=request.user)
    if bills:
        bill_count = len(bills.keys())
        messages.add_message(request, messages.SUCCESS, "%d Bill(s) Generated" % bill_count)
    else:
        messages.add_message(request, messages.ERROR, "0 Bills Generated")
    if 'next' in request.POST:
        return HttpResponseRedirect(request.POST.get('next'))
    if bill_count == 1:
        # If there is only one bill, send them to the bill view page
        bill_id = bills[bills.keys()[0]]['bill'].id
        return HttpResponseRedirect(reverse('staff:billing:bill', kwargs={'bill_id': bill_id}))
    return HttpResponseRedirect(reverse('staff:billing:bills'))


@staff_member_required
def action_record_payment(request):
    # Process our payment form
    bill_id = None
    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        bill_id = payment_form['bill_id'].value()
        try:
            if payment_form.is_valid():
                payment = payment_form.save(created_by=request.user.username)
                messages.success(request, "Payment of $%s recorded." % payment.amount)
        except Exception as e:
            messages.error(request, str(e))
    else:
        raise Exception("Must be a POST!")
    if 'next' in request.POST:
        return HttpResponseRedirect(request.POST.get('next'))
    if bill_id:
        return HttpResponseRedirect(reverse('staff:billing:bill', kwargs={'bill_id': bill_id}))
    return HttpResponseRedirect(reverse('staff:billing:bills'))

@staff_member_required
def bill_view(request, bill_id):
    bill = get_object_or_404(UserBill, id=bill_id)

    if request.method == 'POST':
        if 'delete_payment_id' in request.POST:
            try:
                payment_id = request.POST.get('delete_payment_id')
                payment = Payment.objects.get(id=payment_id)
                payment.delete()
                messages.success(request, "Payment deleted.")
            except Exception as e:
                messages.error(request, str(e))
        if 'mark_paid' in request.POST:
            bill.mark_paid = True
            bill.save()
            messages.success(request, "Bill marked as paid.")

    initial_data = {
        'bill_id': bill.id,
        'username': bill.user.username,
        'payment_date': localtime(now()),
        'amount': bill.total_owed,
    }
    payment_form = PaymentForm(initial=initial_data)

    # Calculate how past due this bill is
    overdue = (localtime(now()).date() - bill.due_date).days
    if overdue < 1:
        overdue = None

    line_items = bill.line_items.all().order_by('id')
    context = {
        'bill': bill,
        'line_items': line_items,
        'overdue': overdue,
        'payment_form': payment_form,
    }
    return render(request, 'staff/billing/bill_view.html', context)

@staff_member_required
def user_bills(request, username):
    user = get_object_or_404(User, username=username)
    bills = user.bills.all().order_by('-due_date')
    return render(request, 'staff/billing/user_bills.html', {'user':user, 'bills':bills})


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
