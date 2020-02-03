import os
import traceback
import logging
import uuid
from weasyprint import HTML, CSS
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import localtime, now
from django.template.loader import get_template

from nadine import email
from nadine.models.alerts import MemberAlert
from nadine.models.profile import FileUpload
from nadine.models.usage import CoworkingDay
from nadine.forms import NewUserForm, MemberSearchForm
from member.models import MOTD
from .forms import SignatureForm

logger = logging.getLogger(__name__)

def motd(request):
    message = MOTD.objects.for_today()
    return render(request, 'tablet/motd.html', {'message': message})

def members(request):
    members = None
    list_members = "startswith" in request.GET
    if list_members:
        sw = request.GET.get('startswith')
        members = User.helper.active_members().filter(first_name__istartswith=sw).order_by('first_name')
    return render(request, 'tablet/members.html', {'members': members, 'list_members': list_members})


def here_today(request):
    users_today = User.helper.here_today().order_by('first_name')
    return render(request, 'tablet/here_today.html', {'users_today': users_today})


def visitors(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                return HttpResponseRedirect(reverse('tablet:post_create', kwargs={'username': user.username}))
        except Exception as e:
            messages.error(request, str(e)[3:len(str(e)) - 2])
            logger.error(str(e))
    else:
        form = NewUserForm()
    return render(request, 'tablet/visitors.html', {'new_user_form': form})


def search(request):
    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            search_results = User.helper.search(member_search_form.cleaned_data['terms'])
    else:
        member_search_form = MemberSearchForm()
    return render(request, 'tablet/search.html', {'member_search_form': member_search_form, 'search_results': search_results})


def user_profile(request, username):
    user = get_object_or_404(User, username=username)

    can_signin = True
    if user.membership.has_desk():
        # They have a desk so they can't sign in
        can_signin = False
    else:
        signins_today = user.coworkingday_set.filter(visit_date=localtime(now()).date()).count()
        if signins_today > 0:
            can_signin = False

    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            search_results = User.helper.search(member_search_form.cleaned_data['terms'], active_only=True)
    else:
        member_search_form = MemberSearchForm()

    # Look up previous hosts for his user
    guest_days = user.coworkingday_set.filter(paid_by__isnull=False).values("paid_by")
    previous_hosts = User.helper.active_members().filter(id__in=guest_days)

    # Pull up how many days were used this period
    days, allowed, billable = user.profile.days_used()

    # Pull our open alerts
    alert_list = [MemberAlert.MEMBER_AGREEMENT, MemberAlert.TAKE_PHOTO, MemberAlert.ORIENTATION, MemberAlert.KEY_AGREEMENT, MemberAlert.ASSIGN_CABINET, MemberAlert.ASSIGN_MAILBOX, MemberAlert.RETURN_DOOR_KEY, MemberAlert.RETURN_DESK_KEY]
    if user.profile.is_active():
        open_alerts = user.profile.open_alerts().filter(key__in=alert_list)
    else:
        open_alerts = None

    context = {
        'user': user,
        'can_signin': can_signin,
        'days_this_period': days,
        'day_allowance': allowed,
        'billable': billable,
        'previous_hosts' :previous_hosts,
        'open_alerts': open_alerts,
        'member_search_form': member_search_form,
        'search_results': search_results,
    }
    return render(request, 'tablet/user_profile.html', context)


def post_create(request, username):
    user = get_object_or_404(User, username=username)
    if "work_today" in request.POST:
        work_today = request.POST.get('work_today')
        if work_today == "Yes":
            # Send them over to the sign-in page.  This will trigger the Free Trial logic down the line.
            return HttpResponseRedirect(reverse('tablet:signin_user', kwargs={'username': user.username}))
        else:
            try:
                email.announce_new_user(user)
            except:
                logger.error("Could not send introduction email to %s" % user.email)
            return HttpResponseRedirect(reverse('tablet:members', kwargs={}))

    search_results = None
    if request.method == "POST":
        member_search_form = MemberSearchForm(request.POST)
        if member_search_form.is_valid():
            search_results = User.helper.search(member_search_form.cleaned_data['terms'], active_only=True)

    return render(request, 'tablet/post_create.html', {'user': user, 'search_results': search_results})


def signin_user(request, username):
    return signin_user_guest(request, username, None)


def signin_user_guest(request, username, paid_by):
    user = get_object_or_404(User, username=username)
    day = CoworkingDay()
    day.user = user
    day.visit_date = localtime(now()).date()
    # Only proceed if they haven't signed in already
    if user.coworkingday_set.filter(visit_date=day.visit_date).count() == 0:
        if paid_by:
            host = get_object_or_404(User, username=paid_by)
            day.paid_by = host
        if user.coworkingday_set.count() == 0:
            day.payment = 'Trial'
        else:
            day.payment = 'Bill'
        day.save()

    return HttpResponseRedirect(reverse('tablet:welcome', kwargs={'username': username}))


def welcome(request, username):
    usage_color = "black"
    user = get_object_or_404(User, username=username)
    first_day = user.coworkingday_set.count() == 1
    days, allowed, billable = user.profile.days_used()
    if days > allowed:
        usage_color = "red"
    elif days == allowed:
        usage_color = "orange"
    else:
        usage_color = "green"
    bill_day_str = user.membership.bill_day_str
    motd = MOTD.objects.for_today()
    context = {
        'user': user,
        'days_this_period': days,
        'day_allowance': allowed,
        'billable': billable,
        'usage_color': usage_color,
        'bill_day_str': bill_day_str,
        'first_day': first_day,
        'motd': motd,
    }
    return render(request, 'tablet/welcome.html', context)


def document_list(request, username):
    user = get_object_or_404(User, username=username)
    # Should be a more elegent way to remove the first element but this works too!
    documents = []
    for key, description in (FileUpload.DOC_TYPES[1], FileUpload.DOC_TYPES[2], FileUpload.DOC_TYPES[3]):
        file_upload = FileUpload.objects.filter(user=user, document_type=key).last()
        documents.append({'key':key, 'description': description, 'file':file_upload})
    context = {'user': user, 'documents': documents}
    return render(request, 'tablet/document_list.html', context)


def document_view(request, username, doc_type):
    user = get_object_or_404(User, username=username)
    file_upload = get_object_or_404(FileUpload, user=user, document_type=doc_type)
    # return render(request, 'tablet/documents_view.html', {'user':user, 'file_upload':file_upload})
    media_url = settings.MEDIA_URL + str(file_upload.file)
    return HttpResponseRedirect(media_url)


def signature_capture(request, username, doc_type):
    user = get_object_or_404(User, username=username)
    today = localtime(now()).date()
    form = SignatureForm(request.POST or None)
    if form and form.has_signature():
        signature_file = form.save_signature()
        render_url = reverse('tablet:sig_render', kwargs={'username': user.username, 'doc_type': doc_type, 'signature_file': signature_file}) + "?save_file=True"
        return HttpResponseRedirect(render_url)
    context = {'user': user, 'form': form, 'today': today, 'doc_type': doc_type}
    return render(request, 'tablet/signature_capture.html', context)


def signature_render(request, username, doc_type, signature_file):
    user = get_object_or_404(User, username=username)
    today = localtime(now()).date()
    pdf_args = {'name': user.get_full_name, 'date': today, 'doc_type': doc_type, 'signature_file': signature_file}
    htmltext = get_template('tablet/signature_render.html')
    signature_html = htmltext.render(pdf_args)
    pdf_file = HTML(string=signature_html, base_url=request.build_absolute_uri()).write_pdf()
    if 'save_file' in request.GET:
        # Save the PDF as a file and redirect them back to the document list
        upload_file = FileUpload.objects.pdf_from_string(user, pdf_file, doc_type, user)
        os.remove(os.path.join(settings.MEDIA_ROOT, "signatures/%s" % signature_file))
        return HttpResponseRedirect(reverse('tablet:document_list', kwargs={'username': user.username}))
    return HttpResponse(pdf_file, content_type='application/pdf')


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
