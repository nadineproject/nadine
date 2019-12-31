from datetime import date, datetime, timedelta
from collections import OrderedDict
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q, Sum
from django.conf import settings

from nadine.models import *
from nadine import email
from nadine.forms import PaymentForm, DateRangeForm


@staff_member_required
def batch_logs(request):
    date_range_form = DateRangeForm.from_request(request, days=7)
    start_date, end_date = date_range_form.get_dates()
    if request.GET.get("run", False):
        batch = BillingBatch.objects.create(created_by=request.user)
        batch.run()
        if not batch.successful:
            messages.error(request, batch.error)
        return HttpResponseRedirect(reverse('staff:billing:batch_logs'))
    bill_id = request.GET.get("bill_id", None)
    if bill_id:
        batches = BillingBatch.objects.filter(bills__id=bill_id)
    else:
        batches = BillingBatch.objects.filter(created_ts__range=(start_date, end_date))
    batches = batches.order_by('created_ts').reverse()
    context = {
        'batches': batches,
        'date_range_form': date_range_form,
        'start_date': start_date,
        'end_date': end_date,
        'bill_id': bill_id,
    }
    return render(request, 'staff/billing/batch_logs.html', context)


@staff_member_required
def bill_list(request):
    date_range_form = DateRangeForm.from_request(request, days=7)
    start_date, end_date = date_range_form.get_dates()
    bills = UserBill.objects.filter(period_start__range=(start_date, end_date)).order_by('period_start').reverse()
    context = {
        'bills': bills,
        'date_range_form': date_range_form,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'staff/billing/bill_list.html', context)


@staff_member_required
def outstanding(request):
    closed_bills = UserBill.objects.outstanding().filter(closed_ts__isnull=False, in_progress=False).order_by('due_date')
    open_bills = UserBill.objects.outstanding().filter(closed_ts__isnull=True, in_progress=False).order_by('due_date')
    in_progress = UserBill.objects.outstanding().filter(in_progress=True).order_by('due_date')
    if closed_bills:
        closed_bills_total = closed_bills.aggregate(total=Sum('bill_total'))['total']
    else:
        closed_bills_total = 0

    if open_bills:
        open_bills_total = open_bills.aggregate(total=Sum('bill_total'))['total']
    else:
        open_bills_total = 0

    if in_progress:
        in_progress_total = in_progress.aggregate(total=Sum('bill_total'))['total']
    else:
        in_progress_total = 0

    subscriptions_due = []
    subscriptions_due_total = 0
    dropins = []
    dropin_total = 0
    other_bills = []
    other_bills_totals = 0
    for bill in open_bills:
        if bill.subscriptions_due:
            subscriptions_due.append(bill)
            subscriptions_due_total += bill.total
        elif bill.subscriptions().count() == 0:
            dropins.append(bill)
            dropin_total += bill.total
        else:
            other_bills.append(bill)
            other_bills_totals += bill.total

    bill_count = closed_bills.count() + open_bills.count() + in_progress.count()
    bill_total = closed_bills_total + open_bills_total + in_progress_total
    context = {
        'closed_bills': closed_bills,
        'subscriptions_due': subscriptions_due,
        'in_progress': in_progress,
        'dropins': dropins,
        'other_bills': other_bills,
        'dropin_total': dropin_total,
        'closed_bills_total': closed_bills_total,
        'subscriptions_due_total': subscriptions_due_total,
        'in_progress_total': in_progress_total,
        'other_bills_totals': other_bills_totals,
        'bill_count': bill_count,
        'bill_total': bill_total,
    }
    return render(request, 'staff/billing/outstanding.html', context)


@staff_member_required
def action_bill_paid(request, bill_id):
    ''' Mark the bill paid '''
    bill = get_object_or_404(UserBill, id=bill_id)
    amount = bill.total
    if 'amount' in request.POST:
        amount = float(request.POST['amount'])
    payment = Payment.objects.create(bill=bill, user=bill.user, amount=amount, created_by=request.user)
    if 'payment_date' in request.POST:
        payment.created_ts = datetime.strptime(request.POST['payment_date'], "%Y-%m-%d").date()
        payment.save()

    messages.success(request, "Bill %d ($%s) paid" % (bill.id, format(amount, '.2f')))
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
def bill_view_redirect(request):
    if "bill_id" in request.POST:
        bill_id = request.POST['bill_id']
        return HttpResponseRedirect(reverse('staff:billing:bill', kwargs={'bill_id': bill_id}))
    raise Http404


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
        if 'close_bill' in request.POST:
            bill.close()
            messages.success(request, "Bill marked as closed.")
        if 'waive_day' in request.POST:
            day_id = request.POST.get('waive_day')
            day = CoworkingDay.objects.get(pk=day_id)
            day.mark_waived()
            bill.recalculate()
            messages.success(request, "Activity on %s waived and bill recalculated." % day.visit_date)
        if 'recalculate' in request.POST:
            bill.recalculate()
            messages.success(request, "Bill recalculated.")

    initial_data = {
        'bill_id': bill.id,
        'username': bill.user.username,
        'payment_date': localtime(now()),
        'amount': bill.total_owed,
        'can_waive_days': bill.total_paid == 0,
    }
    payment_form = PaymentForm(initial=initial_data)

    # Calculate how past due this bill is
    overdue = (localtime(now()).date() - bill.due_date).days
    if overdue < 1:
        overdue = None

    # Count up all the resources on this bill
    resources = {}
    if bill.coworking_day_count > 0 or bill.coworking_day_allowance > 0:
        resources['days'] = {
            'count': bill.coworking_day_count,
            'billable': bill.coworking_day_billable_count,
            'allowance': bill.coworking_day_allowance,
            'overage': bill.coworking_day_overage,
        }
    if bill.desk_allowance:
        resources['desk'] = bill.desk_allowance
    if bill.mail_allowance:
        resources['mail'] = bill.mail_allowance
    if bill.key_allowance:
        resources['key'] = bill.key_allowance

    line_items = bill.line_items.all().order_by('id')
    context = {
        'bill': bill,
        'line_items': line_items,
        'resources': resources,
        'overdue': overdue,
        'payment_form': payment_form,
    }
    return render(request, 'staff/billing/bill_view.html', context)

@staff_member_required
def user_bills(request, username):
    user = get_object_or_404(User, username=username)
    bills = user.bills.all().order_by('-due_date')
    return render(request, 'staff/billing/user_bills.html', {'user':user, 'bills':bills})


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
