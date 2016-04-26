from datetime import date, datetime, timedelta
from collections import OrderedDict

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

from decimal import Decimal

from nadine.models import *
from staff.forms import PayBillsForm
from staff import email

@staff_member_required
def transactions(request):
    page_message = None
    start, end = date_range_from_request(request)
    date_range_form = DateRangeForm({START_DATE_PARAM: start, END_DATE_PARAM: end})
    transactions = Transaction.objects.filter(transaction_date__range=(start, end)).order_by('-transaction_date')
    return render_to_response('staff/transactions.html', {"transactions": transactions, 'date_range_form': date_range_form, 'page_message': page_message}, context_instance=RequestContext(request))


@staff_member_required
def transaction(request, id):
    transaction = get_object_or_404(Transaction, pk=id)
    return render_to_response('staff/transaction.html', {"transaction": transaction}, context_instance=RequestContext(request))


def run_billing(request):
    page_message = None
    run_billing_form = RunBillingForm(initial={'run_billing': True})
    if request.method == 'POST':
        run_billing_form = RunBillingForm(request.POST)
        if run_billing_form.is_valid():
            billing.run_billing()
            page_message = 'At your request, I have run <a href="%s">the bills</a>.' % (reverse('staff.views.billing.bills', args=[], kwargs={}),)
    logs = BillingLog.objects.all()[:10]
    return render_to_response('staff/run_billing.html', {'run_billing_form': run_billing_form, 'page_message': page_message, "billing_logs": logs}, context_instance=RequestContext(request))


@staff_member_required
def bills(request):
    page_message = None
    if request.method == 'POST':
        pay_bills_form = PayBillsForm(request.POST)
        if pay_bills_form.is_valid():
            try:
                member = Member.objects.get(pk=int(pay_bills_form.cleaned_data['member_id']))
            except:
                page_message = 'Error: I could not find that user.'

            amount = pay_bills_form.cleaned_data['amount']
            if page_message == None:
                bill_ids = [int(bill_id) for bill_id in request.POST.getlist('bill_id')]
                transaction = Transaction(member=member, status='closed', amount=Decimal(amount))
                transaction.note = pay_bills_form.cleaned_data['transaction_note']
                transaction.save()
                for bill in member.open_bills():
                    if bill.id in bill_ids:
                        transaction.bills.add(bill)
                page_message = 'Created a <a href="%s">transaction for %s</a>' % (reverse('staff.views.billing.transaction', args=[], kwargs={'id': transaction.id}), member,)

    bills = {}
    members = Member.objects.filter(models.Q(bills__isnull=False, bills__transactions=None, bills__paid_by__isnull=True) | models.Q(guest_bills__isnull=False, guest_bills__transactions=None)).distinct().order_by('user__last_name')
    for member in members:
        last_bill = member.open_bills()[0]
        if not last_bill.bill_date in bills:
            bills[last_bill.bill_date] = []
        bills[last_bill.bill_date].append(member)
    ordered_bills = OrderedDict(sorted(bills.items(), key=lambda t: t[0]))

    invalids = Member.objects.invalid_billing()
    return render_to_response('staff/bills.html', {'bills': ordered_bills, 'page_message': page_message, 'invalid_members': invalids}, context_instance=RequestContext(request))

@staff_member_required
def bills_pay_all(request, username):
    user = get_object_or_404(User, username=username)
    member = user.get_profile()
    amount = member.open_bill_amount()

    # Save all the bills!
    if amount > 0:
        transaction = Transaction(member=member, status='closed', amount=amount)
        transaction.save()
        for bill in member.open_bills():
            transaction.bills.add(bill)

    # Where to next?
    if request.method == 'POST':
        if 'next' in request.POST:
            next_url = request.POST.get("next")
        else:
            next_url = reverse('staff.views.billing.bills')

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
    return render_to_response('staff/bill_list.html', {'bills': bills, 'total_amount': total_amount, 'date_range_form': date_range_form, 'start_date': start_date, 'end_date': end_date}, context_instance=RequestContext(request))


@staff_member_required
def toggle_billing_flag(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    user = member.user

    page_message = member.full_name + " billing profile: "
    if member.valid_billing:
        page_message += " Invalid"
        member.valid_billing = False
        member.save()
        email.send_invalid_billing(user)
    else:
        page_message += " Valid"
        member.valid_billing = True
        member.save()

    if 'back' in request.POST:
        return HttpResponseRedirect(request.POST.get('back'))
    return HttpResponseRedirect(reverse('staff.views.billing.bills'))


@staff_member_required
def bill(request, id):
    bill = get_object_or_404(Bill, pk=id)
    return render_to_response('staff/bill.html', {"bill": bill, 'new_member_deposit': settings.NEW_MEMBER_DEPOSIT}, context_instance=RequestContext(request))
