from . import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, transaction
from django.forms.formsets import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.timezone import localtime, now

from nadine import email
from nadine.models.profile import UserProfile, FileUpload
from nadine.models.usage import CoworkingDay, Event
from nadine.models.resource import Resource
from nadine.models.billing import UserBill
from nadine.models.alerts import MemberAlert
from nadine.models.organization import Organization, OrganizationMember
from nadine.models.membership import Membership, ResourceSubscription
from nadine.forms import EditProfileForm, ProfileImageForm, LinkForm, BaseLinkFormSet
from nadine.utils import network
from nadine.utils.payment_api import PaymentAPI
from arpwatch import arp
from arpwatch.models import ArpLog, UserDevice
from member.views.core import is_active_member


@login_required
def profile_redirect(request):
    return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.user.username}))


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    emergency_contact = user.get_emergency_contact()
    current_org_memberships = user.profile.active_organization_memberships()
    past_org_memberships = user.profile.past_organization_memberships()
    can_edit = request.user == user or request.user.is_staff
    today = localtime(now()).date()
    has_bookings = User.objects.filter(username=user.username).filter(event__start_ts__gte=today)

    ALLOW_PHOTO_UPLOAD = settings.ALLOW_PHOTO_UPLOAD
    if request.user.is_staff:
        ALLOW_PHOTO_UPLOAD = True

    context = {'user': user,
               'emergency_contact': emergency_contact,
               'settings': settings,
               'ALLOW_PHOTO_UPLOAD': ALLOW_PHOTO_UPLOAD,
               'can_edit': can_edit,
               'current_org_memberships': current_org_memberships, 'past_org_memberships': past_org_memberships,
               'has_bookings': has_bookings,
               }
    return render(request, 'member/profile/profile.html', context)


@login_required
def profile_private(request, username):
    user = get_object_or_404(User, username=username)
    context = {'user': user}
    return render(request, 'member/profile/profile_private.html', context)


@login_required
def profile_membership(request, username):
    user = get_object_or_404(User, username=username)
    memberships = ResourceSubscription.objects.filter(membership=user.membership.id)
    context = {'user': user,
               'memberships': memberships,}
    return render(request, 'member/profile/profile_membership.html', context)


@login_required
def profile_documents(request, username):
    user = get_object_or_404(User, username=username)
    context = {'user': user}
    return render(request, 'member/profile/profile_documents.html', context)


@login_required
def profile_events(request, username):
    user = get_object_or_404(User, username=username)
    today = localtime(now()).date()
    upcoming_events = Event.objects.filter(user=user).filter(start_ts__gte=today)
    upcoming = []
    hours_subscriptions = 0
    if ResourceSubscription.objects.filter(membership=user.membership, resource=Resource.objects.event_resource):
        hours_subscriptions = ResourceSubscription.objects.get(membership=user.membership, resource=Resource.objects.event_resource).allowance

    for e in upcoming_events:
        total = ((e.end_ts - e.start_ts).total_seconds())/3600
        upcoming.append({'name': e.description, 'start_ts': e.start_ts, 'end_ts': e.end_ts, 'room': e.room, 'total': total})

    ps, pe = user.membership.get_period()
    this_period = Event.objects.filter(user=user).filter(start_ts__gte=ps).filter(end_ts__lte=pe)
    total = 0
    for t in this_period:
        total += ((t.end_ts - t.start_ts).total_seconds()/3600)
    context = {'user': user,
               'upcoming': upcoming,
               'total': total,
               'hours_subscriptions': hours_subscriptions,
                }
    return render(request, 'member/profile/profile_events.html', context)


@login_required
def profile_activity(request, username):
    user = get_object_or_404(User.objects.select_related('profile'), username=username)
    membership = Membership.objects.for_user(user)
    period_start, period_end = membership.get_period()
    days_this_period = membership.coworking_days_in_period()
    days, allowance, billable = user.profile.days_used()
    show_user = False
    show_paid = False
    for d in days_this_period:
        if d.user != user:
            show_user = True
        if d.paid_by:
            show_paid = True
    context = {
        'user': user,
        'period_start': period_start,
        'period_end': period_end,
        'show_user': show_user,
        'show_paid': show_paid,
        'days_this_period': days_this_period,
        'allowance': allowance,
        'billable': billable,

    }
    return render(request, 'member/profile/profile_activity.html', context)


@login_required
def profile_billing(request, username):
    user = get_object_or_404(User, username=username)
    bills = UserBill.objects.filter(user=user).order_by('-due_date')[:12]
    context = {
        'user': user,
        'bills': bills,
        'settings': settings,
    }
    return render(request, 'member/profile/profile_billing.html', context)


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    if not user == request.user:
        if not request.user.is_staff:
            return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.user.username}))

    LinkFormSet = formset_factory(LinkForm, formset=BaseLinkFormSet)

    user_links = user.profile.websites.all()
    link_data = [{'url_type': l.url_type, 'url': l.url, 'username': user.username} for l in user_links]

    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST)
        link_formset = LinkFormSet(request.POST)
        profile_form.public_profile = request.POST['public_profile']

        if profile_form.is_valid():
            if link_formset.is_valid():
                if request.POST.get('password-create') == request.POST.get('password-confirm'):
                    pwd = request.POST.get('password-create')

                    if len(pwd.strip()) > 0:
                        if pwd.strip() == pwd and len(pwd) > 7:

                            profile_form.save()
                            user.set_password(pwd)
                            user.save()

                            return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))
                        else:
                            messages.error(request, 'Your password must be at least 8 characters long.')
                    else:
                        for link in link_data:
                            del_url = link.get('url')
                            user.profile.websites.filter(url=del_url).delete()

                        for link_form in link_formset:
                            if not link_form.cleaned_data.get('username'):
                                link_form.cleaned_data['username'] = user.username
                            try:
                                if link_form.is_valid():
                                    url_type = link_form.cleaned_data.get('url_type')
                                    url = link_form.cleaned_data.get('url')
                                    if url_type and url:
                                        link_form.save()
                            except Exception as e:
                                messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))
                        profile_form.save()

                        return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))
                else:
                    messages.error(request,'The entered passwords do not match. Please try again.')
            else:
                messages.error(request, 'There was an error saving your websites. Please make sure they have a valid URL and URL type.')
    else:
        link_formset = LinkFormSet(initial=link_data)
        profile = user.profile
        emergency_contact = user.get_emergency_contact()
        profile_form = EditProfileForm(initial={'username': user.username,
                                                'first_name': user.first_name,
                                                'last_name': user.last_name,
                                                'email': user.email,
                                                'phone': profile.phone, 'phone2': profile.phone2,
                                                'address1': profile.address1, 'address2': profile.address2, 'city': profile.city, 'state': profile.state, 'zipcode': profile.zipcode,
                                                'url_personal': profile.url_personal, 'url_professional': profile.url_professional,
                                                'url_facebook': profile.url_facebook, 'url_twitter': profile.url_twitter,
                                                'url_linkedin': profile.url_linkedin, 'url_github': profile.url_github,
                                                'bio': profile.bio, 'photo': profile.photo,
                                                'public_profile': profile.public_profile,
                                                'gender': profile.gender, 'pronouns': profile.pronouns,
                                                'howHeard': profile.howHeard, 'industry': profile.industry, 'neighborhood': profile.neighborhood,
                                                'has_kids': profile.has_kids, 'self_employed': profile.self_employed,
                                                'emergency_name': emergency_contact.name, 'emergency_relationship': emergency_contact.relationship,
                                                'emergency_phone': emergency_contact.phone, 'emergency_email': emergency_contact.email,
                                                })

    context = {'user': user, 'profile_form': profile_form, 'link_formset': link_formset}
    return render(request, 'member/profile/profile_edit.html', context)


@login_required
def user_devices(request, username):
    user = get_object_or_404(User, username=username)
    if not user == request.user and not request.user.is_staff:
        return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.user.username}))

    error = None
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        device = UserDevice.objects.get(id=device_id)

        action = request.POST.get('action')
        if action == "Register":
            device.user = user

        device_name = request.POST.get('device_name')
        device_name = device_name.strip()[:32]
        device.device_name = device_name
        device.save()
        return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.user.username}))

    devices = user.userdevice_set.all()
    ip = network.get_addr(request)
    this_device = arp.device_by_ip(ip)

    context = {'user': user,
               'devices': devices,
               'this_device': this_device,
               'ip': ip,
               'error': error,
               'settings': settings
               }
    return render(request, 'member/profile/profile_devices.html', context)


@login_required
def disable_billing(request, username):
    user = get_object_or_404(User, username=username)
    if user == request.user or request.user.is_staff:
        api = PaymentAPI()
        api.disable_recurring(username)
        email.announce_billing_disable(user)
    return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def file_view(request, disposition, username, file_name):
    if not request.user.is_staff and not username == request.user.username:
        return HttpResponseForbidden("Forbidden")
    file_upload = FileUpload.objects.filter(user__username=username, name=file_name).first()
    if not file_upload:
        raise Http404
    if disposition is None or not (disposition == "inline" or disposition == "attachment"):
        disposition = "inline"
    response = HttpResponse(file_upload.file, content_type=file_upload.content_type)
    response['Content-Disposition'] = '%s; filename="%s"' % (disposition, file_upload.name)
    return response

@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def edit_photo(request, username):
    user = get_object_or_404(User, username=username)
    if not user == request.user and not request.user.is_staff:
        return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.user.username}))

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))
            else:
                print(form)
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))
    else:
        form = ProfileImageForm()

    context = {'user': user, 'form': form}
    return render(request, 'member/profile/profile_image_edit.html', context)

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
