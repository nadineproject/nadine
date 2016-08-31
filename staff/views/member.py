import os
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

from monthdelta import MonthDelta, monthmod

from staff import email
from staff.forms import MemberEditForm, MembershipForm
from nadine.models import Member, Membership, MemberNote, MembershipPlan, DailyLog, SentEmailLog, FileUpload, SpecialDay


@staff_member_required
def edit(request, username):
    user = get_object_or_404(User, username=username)

    if request.method == 'POST':
        edit_form = MemberEditForm(request.POST, request.FILES)
        if edit_form.is_valid():
            try:
                edit_form.save()
                messages.add_message(request, messages.INFO, "Member Updated")
                return HttpResponseRedirect(reverse('staff.views.member.detail_user', args=[], kwargs={'username': username}))
            except Exception as e:
                messages.add_message(request, messages.ERROR, e)
    else:
        emergency_contact = user.get_emergency_contact()
        member_data={'username': username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'email2': user.profile.email2,
            'phone': user.profile.phone,
            'phone2': user.profile.phone2,
            'address1': user.profile.address1,
            'address2': user.profile.address2,
            'city': user.profile.city,
            'state': user.profile.state,
            'zipcode': user.profile.zipcode,
            'company_name': user.profile.company_name,
            'url_personal': user.profile.url_personal,
            'url_professional': user.profile.url_professional,
            'url_facebook': user.profile.url_facebook,
            'url_twitter': user.profile.url_twitter,
            'url_linkedin': user.profile.url_linkedin,
            'url_github': user.profile.url_github,
            'url_aboutme': user.profile.url_aboutme,
            'gender': user.profile.gender,
            'howHeard': user.profile.howHeard,
            'industry': user.profile.industry,
            'neighborhood': user.profile.neighborhood,
            'has_kids': user.profile.has_kids,
            'self_employed': user.profile.self_employed,
            'photo': user.profile.photo,
            'emergency_name': emergency_contact.name,
            'emergency_relationship': emergency_contact.relationship,
            'emergency_phone': emergency_contact.phone,
            'emergency_email': emergency_contact.email,
        }
        edit_form = MemberEditForm(initial=member_data)

    return render_to_response('staff/member_edit.html', { 'user':user, 'member':user.profile, 'edit_form': edit_form }, context_instance=RequestContext(request))


@staff_member_required
def detail_user(request, username):
    user = get_object_or_404(User, username=username)
    return HttpResponseRedirect(reverse('staff.views.member.detail', args=[], kwargs={'member_id': user.profile.id}))


@staff_member_required
def detail(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    #daily_logs = DailyLog.objects.filter(member=member).order_by('visit_date').reverse()
    emergency_contact = member.user.get_emergency_contact()
    memberships = Membership.objects.filter(member=member).order_by('start_date').reverse()
    email_logs = SentEmailLog.objects.filter(member=member).order_by('created').reverse()

    if request.method == 'POST':
        if 'send_manual_email' in request.POST:
            key = request.POST.get('message_key')
            email.send_manual(member.user, key)
        elif 'add_note' in request.POST:
            note = request.POST.get('note')
            MemberNote.objects.create(user=member.user, member=member, created_by=request.user, note=note)
        elif 'add_special_day' in request.POST:
            month = request.POST.get('month')
            day = request.POST.get('day')
            year = request.POST.get('year')
            if len(year) == 0:
                year = None
            desc = request.POST.get('description')
            SpecialDay.objects.create(user=member.user, member=member, month=month, day=day, year=year, description=desc)
        else:
            print(request.POST)

    email_keys = email.valid_message_keys()
    email_keys.remove("all")

    return render_to_response('staff/member_detail.html', {'member': member, 'emergency_contact': emergency_contact,
        'memberships': memberships, 'email_logs': email_logs, 'email_keys': email_keys, 'settings': settings}, context_instance=RequestContext(request))



@staff_member_required
def transactions(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    return render_to_response('staff/member_transactions.html', {'member': member}, context_instance=RequestContext(request))


@staff_member_required
def bills(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    return render_to_response('staff/member_bills.html', {'member': member}, context_instance=RequestContext(request))


@staff_member_required
def signins(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    payment_types = ['Visit', 'Trial', 'Waive', 'Bill']
    return render_to_response('staff/member_signins.html', {'payment_types': payment_types, 'member': member}, context_instance=RequestContext(request))


@staff_member_required
def signins_json(request, member_id):
    member = get_object_or_404(Member, pk=member_id)
    response_data = {}
    #response_data['member'] = model_to_dict(member)
    #response_data['payment_types'] = ['Visit', 'Trial', 'Waive', 'Bill']
    response_data['daily_logs'] = serializers.serialize('json', member.daily_logs.all())
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@staff_member_required
def files(request, member_id):
    member = get_object_or_404(Member, pk=member_id)

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
            #upload_obj = FileUpload(user=file_user, file=upload, name=file_name, document_type=doc_type, content_type=upload.content_type, uploaded_by=request.user)
            # upload_obj.save()
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not upload file: (%s)" % e)

    doc_types = FileUpload.DOC_TYPES
    files = FileUpload.objects.filter(user=member.user)
    return render_to_response('staff/member_files.html', {'member': member, 'files': files, 'doc_types': doc_types}, context_instance=RequestContext(request))


@staff_member_required
def membership(request, member_id):
    member = get_object_or_404(Member, pk=member_id)

    start = today = timezone.localtime(timezone.now()).date()
    last_membership = member.last_membership()
    if last_membership and last_membership.end_date and last_membership.end_date > today - timedelta(days=10):
        start = (member.last_membership().end_date + timedelta(days=1))
    last = start + MonthDelta(1) - timedelta(days=1)

    if request.method == 'POST':
        membership_form = MembershipForm(request.POST, request.FILES)
        try:
            if membership_form.is_valid():
                membership_form.created_by = request.user
                membership_form.save()
                return HttpResponseRedirect(reverse('staff.views.member.detail', args=[], kwargs={'member_id': member.id}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, e)
    else:
        membership_form = MembershipForm(initial={'member': member_id, 'start_date': start})

    # Send them to the update page if we don't have an end date
    if (member.last_membership() and not member.last_membership().end_date):
        return HttpResponseRedirect(reverse('staff.views.core.membership', args=[], kwargs={'membership_id': member.last_membership().id}))
    plans = MembershipPlan.objects.filter(enabled=True).order_by('name')
    return render_to_response('staff/membership.html', {'member': member, 'membership_plans': plans,
                                                        'membership_form': membership_form, 'today': today.isoformat(), 'last': last.isoformat()}, context_instance=RequestContext(request))
