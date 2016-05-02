from datetime import date, datetime, timedelta

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

from nadine.models import Member, XeroContact

from py4j.java_gateway import JavaGateway
from nadine.utils.xero_api import XeroAPI
from nadine.utils.usaepay_api import EPayAPI
from nadine.utils.payment_api import PaymentAPI


@staff_member_required
def xero_user(request, username):
    user = get_object_or_404(User, username=username)
    xero_api = XeroAPI()

    if request.method == 'POST':
        action = request.POST.get('action').lower()
        if action == "link":
            if 'xero_id' in request.POST:
                xero_id = request.POST.get('xero_id').strip()
                if len(xero_id) > 0:
                    try:
                        if len(xero_api.xero.contacts.get(xero_id)) == 1:
                            XeroContact.objects.create(user=user, xero_id=xero_id)
                    except Exception:
                        pass
        elif action == "sync" or action == "add":
            xero_api.sync_user_data(user)

    invoices = None
    repeating_invoices = None
    xero_contact_data = None
    xero_contact_search = None
    xero_contact = XeroContact.objects.filter(user=user).first()
    if not xero_contact:
        xero_contact_search = xero_api.find_contacts(user)
    else:
        invoices = xero_api.get_invoices(user)
        invoices.reverse()
        repeating_invoices = xero_api.get_repeating_invoices(user)
        xero_contact_data = xero_api.get_contact(user)
    return render_to_response('staff/xero.html', {'user': user, 'xero_contact': xero_contact, 'invoices': invoices, 'repeating_invoices':repeating_invoices,
        'xero_contact_data': xero_contact_data, 'xero_contact_search': xero_contact_search}, context_instance=RequestContext(request))


@staff_member_required
def usaepay_user(request, username):
    user = get_object_or_404(User, username=username)

    # When we add a card we POST to USAePay and it comes back to this page
    # Any errors will be communicated to us in this GET variable
    if 'UMerror' in request.GET:
        messages.add_message(request, messages.ERROR, request.GET.get('UMerror'))

    history = None
    try:
        api = PaymentAPI()

        if 'disable_all' in request.POST:
            api.disableAutoBilling(username)

        customer_id = request.POST.get("customer_id", None)
        action = request.POST.get("action", "")
        #print "action: %s" % action
        #print "cust: %s " % customer_id
        if customer_id:
            if action == "verify_profile":
                # Run a $1.00 authorization to verify this profile works
                api.run_transaction(customer_id, 1.00, "Office Nomads Authorization", auth_only=True)
                messages.add_message(request, messages.INFO, "Payment for %s successfully authorized" % username)
            elif action == "delete_profile":
                # TODO
                messages.add_message(request, messages.INFO, "Billing profile deleted for %s" % username)
            elif action == "manual_charge":
                invoice = request.POST.get("invoice")
                description = request.POST.get("description")
                amount = request.POST.get("amount")
                comment = request.POST.get("comment")
                api.run_transaction(customer_id, amount, description, invoice=invoice, comment=comment)
                messages.add_message(request, messages.INFO, "Sale for %s successfully authorized" % username)
            elif action == "edit_recurring":
                next_date = request.POST.get("next_date")
                description = request.POST.get("description")
                comment = request.POST.get("comment")
                amount = request.POST.get("amount")
                enabled = request.POST.get("enabled", "") == "on"
                api.update_recurring(customer_id, enabled, next_date, description,comment, amount)
                messages.add_message(request, messages.INFO, "Recurring billing updated for %s" % username)

        # Lastly pull all customers for this user
        history = api.get_history(username)
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)

    return render_to_response('staff/usaepay.html', {'user': user, 'history': history, 'settings':settings }, context_instance=RequestContext(request))


@staff_member_required
def usaepay_transactions_today(request):
    today = timezone.localtime(timezone.now())
    return HttpResponseRedirect(reverse('staff.views.payment.usaepay_transactions', args=[], kwargs={'year': today.year, 'month': today.month, 'day': today.day}))


@staff_member_required
def usaepay_transactions(request, year, month, day):
    d = date(year=int(year), month=int(month), day=int(day))
    open_batch = False
    amex = []
    visamc = []
    ach = []
    settled_checks = []
    other_transactions = []
    totals = {'amex_total':0, 'visamc_total':0, 'ach_total':0, 'total':0}
    open_xero_invoices = XeroAPI().get_open_invoices_by_user()
    try:
        api = PaymentAPI()

        if 'close_batch' in request.GET:
            api.close_current_batch()
            messages.add_message(request, messages.INFO, "Current batch closed")

        transactions = api.get_transactions(year, month, day)
        totals['total_count'] = len(transactions)

        # Pull the settled checks seperately
        # TODO - using the old api for now -- REMOVE!
        settled_checks = EPayAPI().get_checks_settled_by_date(year, month, day)
        #settled_checks = api.get_checks_settled_by_date(year, month, day)

        for t in transactions:
            # Pull the member and the amount they owe
            member = Member.objects.filter(user__username = t['username']).first()
            if member:
                t['member'] = member
                t['open_bill_amount'] = member.open_bill_amount()
                t['xero_invoices'] = open_xero_invoices.get(t['username'], [])
                for i in t['xero_invoices']:
                    if i['AmountDue'] != t['amount']:
                        t['xero_invoices'].remove(i)

            # Total up all the Settled transactions
            if t['transaction_type'] == "Sale" and t['status'] != "Declined" and t['status'] != "Error":
                totals['total'] = totals['total'] + t['amount']
                if t['card_type'] == "A":
                    amex.append(t)
                    totals['amex_total'] = totals['amex_total'] + t['amount']
                elif t['card_type'] == "V" or t['card_type'] == "M":
                    visamc.append(t)
                    totals['visamc_total'] = totals['visamc_total'] + t['amount']
                elif t['card_type'] == "ACH":
                    ach.append(t)
                    totals['ach_total'] = totals['ach_total'] + t['amount']

                # Presence of authorized transactions means this batch is still open
                if t['status'] == "Authorized":
                    open_batch = True
            else:
                other_transactions.append(t)


    except Exception as e:
        messages.add_message(request, messages.ERROR, e)

    return render_to_response('staff/charges.html', {'date': d, 'amex': amex, 'visamc': visamc, 'ach':ach, 'open_batch':open_batch,
                                                      'other_transactions': other_transactions, 'settled_checks':settled_checks, 'totals':totals,
                                                      'next_date': d + timedelta(days=1), 'previous_date': d - timedelta(days=1)}, context_instance=RequestContext(request))


@staff_member_required
def usaepay_members(request):
    members = []
    api = PaymentAPI()
    for m in Member.objects.active_members():
        username = m.user.username
        customers = api.get_customers(username)
        if customers:
            for c in customers:
                if c.Enabled:
                    members.append({'member': m, 'username': username, 'next': c.Next, 'customer_number': c.CustNum})
    return render_to_response('staff/usaepay_members.html', {'members': members}, context_instance=RequestContext(request))


@staff_member_required
def usaepay_void(request):
    transaction = None
    try:
        api = PaymentAPI()
        if 'transaction_id' in request.POST:
            transaction_id = int(request.POST.get('transaction_id'))
            transaction = api.get_transaction(transaction_id)

            if 'username' in request.POST and 'confirmed' in request.POST:
                username = request.POST.get('username')
                api.void_transaction(username, transaction_id)
                messages.add_message(request, messages.INFO, "Transaction for %s voided" % username)
                return HttpResponseRedirect(reverse('staff.views.payment.usaepay_transactions_today'))
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)

    return render_to_response('staff/usaepay_void.html', {'transaction':transaction}, context_instance=RequestContext(request))
