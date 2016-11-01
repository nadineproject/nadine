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
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import Q, Sum
from django.conf import settings

from decimal import Decimal

from nadine.models import *
from nadine import email
from nadine.forms import PayBillsForm, RunBillingForm, DateRangeForm
from staff.views.activity import date_range_from_request, START_DATE_PARAM, END_DATE_PARAM
from staff import billing


@staff_member_required
def transactions(request):
    page_message = None
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    transactions = Transaction.objects.filter(transaction_date__range=(start, end)).order_by('-transaction_date')
    context = {"transactions": transactions, 'date_range_form': date_range_form, 'page_message': page_message}
    return render(request, 'staff/transactions.html', context)


@staff_member_required
def transaction(request, id):
    transaction = get_object_or_404(Transaction, pk=id)
    return render(request, 'staff/transaction.html', {"transaction": transaction})


def run_billing(request):
    page_message = None
    run_billing_form = RunBillingForm(initial={'run_billing': True})
    if request.method == 'POST':
        run_billing_form = RunBillingForm(request.POST)
        if run_billing_form.is_valid():
            billing.run_billing()
            page_message = 'At your request, I have run <a href="%s">the bills</a>.' % (reverse('staff_bills', args=[], kwargs={}),)
    logs = BillingLog.objects.all()[:10]
    context = {'run_billing_form': run_billing_form, 'page_message': page_message, "billing_logs": logs}
    return render(request, 'staff/run_billing.html', context)


@staff_member_required
def bills(request):
    page_message = None
    if request.method == 'POST':
        pay_bills_form = PayBillsForm(request.POST)
        if pay_bills_form.is_valid():
            try:
                user = User.objects.get(username=pay_bills_form.cleaned_data['username'])
            except:
                page_message = 'Error: I could not find that user.'

            amount = pay_bills_form.cleaned_data['amount']
            if page_message == None:
                bill_ids = [int(bill_id) for bill_id in request.POST.getlist('bill_id')]
                transaction = Transaction(user=user, status='closed', amount=Decimal(amount))
                transaction.note = pay_bills_form.cleaned_data['transaction_note']
                transaction.save()
                for bill in user.profile.open_bills():
                    if bill.id in bill_ids:
                        transaction.bills.add(bill)
                transaction_url = reverse('staff_transaction', args=[], kwargs={'id': transaction.id})
                page_message = 'Created a <a href="%s">transaction for %s</a>' % (transaction_url, user.get_full_name())

    bills = {}
    unpaid = models.Q(bill__isnull=False, bill__transactions=None, bill__paid_by__isnull=True)
    unpaid_guest = models.Q(guest_bills__isnull=False, guest_bills__transactions=None)
    users = User.objects.filter(unpaid | unpaid_guest).distinct().order_by('last_name')
    for u in users:
        last_bill = u.profile.open_bills()[0]
        if not last_bill.bill_date in bills:
            bills[last_bill.bill_date] = []
        bills[last_bill.bill_date].append(u)
    ordered_bills = OrderedDict(sorted(bills.items(), key=lambda t: t[0]))
    invalids = User.helper.invalid_billing()

    context = {'bills': ordered_bills, 'page_message': page_message, 'invalid_members': invalids}
    return render(request, 'staff/bills.html', context)


@staff_member_required
def bills_pay_all(request, username):
    user = get_object_or_404(User, username=username)
    amount = user.profile.open_bill_amount()

    # Save all the bills!
    if amount > 0:
        transaction = Transaction(user=user, status='closed', amount=amount)
        transaction.save()
        for bill in user.profile.open_bills():
            transaction.bills.add(bill)

    # Where to next?
    if request.method == 'POST':
        if 'next' in request.POST:
            next_url = request.POST.get("next")
        else:
            next_url = reverse('staff_bills')

    return HttpResponseRedirect(next_url)


@staff_member_required
def bill_list(request):
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    starteo = timeo.strptime(start, "%Y-%m-%d")
    start_date = date(year=starteo.tm_year, month=starteo.tm_mon, day=starteo.tm_mday)
    endeo = timeo.strptime(end, "%Y-%m-%d")
    end_date = date(year=endeo.tm_year, month=endeo.tm_mon, day=endeo.tm_mday)
    bills = Bill.objects.filter(bill_date__range=(start_date, end_date), amount__gt=0).order_by('bill_date').reverse()
    total_amount = bills.aggregate(s=Sum('amount'))['s']
    context = {'bills': bills, 'total_amount': total_amount,
        'date_range_form': date_range_form, 'start_date': start_date, 'end_date': end_date}
    return render(request, 'staff/bill_list.html', context)


@staff_member_required
def toggle_billing_flag(request, username):
    user = get_object_or_404(User, username=username)

    page_message = user.get_full_name() + " billing profile: "
    if user.profile.valid_billing:
        page_message += " Invalid"
        user.profile.valid_billing = False
        email.send_invalid_billing(user)
    else:
        page_message += " Valid"
        user.profile.valid_billing = True
    user.profile.save()

    if 'back' in request.POST:
        return HttpResponseRedirect(request.POST.get('back'))
    return HttpResponseRedirect(reverse('staff_bills'))


@staff_member_required
def bill(request, id):
    bill = get_object_or_404(Bill, pk=id)
    context = {"bill": bill, 'new_member_deposit': settings.NEW_MEMBER_DEPOSIT}
    return render(request, 'staff/bill.html', context)
