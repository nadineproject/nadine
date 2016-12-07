import string

from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from nadine.forms import OrganizationForm, OrganizationMemberForm, OrganizationSearchForm
from nadine.models.organization import Organization, OrganizationMember

from members.views.core import is_active_member


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_list(request):
    orgs = Organization.objects.active_organizations()

    search_terms = None
    search_results = None
    if request.method == "POST":
        search_form = OrganizationSearchForm(request.POST)
        if search_form.is_valid():
            search_terms = search_form.cleaned_data['terms']
            search_results = Organization.objects.search(search_terms)

    else:
        search_form = OrganizationSearchForm()

    context = {'organizations': orgs, 'search_results': search_results,
        'search_form': search_form, 'search_terms': search_terms, }
    return render(request, 'members/org_list.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_view(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    can_edit = org.can_edit(request.user) or request.user.is_staff

    members = org.organizationmember_set.all().order_by('start_date')
    counts = { 'total': members.count(), 'active': 0, 'inactive': 0 }
    for m in members:
        if m.is_active():
            counts['active'] = counts['active'] + 1
        else:
            counts['inactive'] = counts['inactive'] + 1

    show_all = 'show_all' in request.GET or counts['active'] == 0
    context = {'organization': org,
        'can_edit':can_edit,
        'members': members,
        'counts': counts,
        'show_all': show_all,
    }
    return render(request, 'members/org_view.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_add(request):
    if not 'org' in request.POST and 'username' in request.POST:
        return HttpResponseForbidden("Forbidden")

    user = get_object_or_404(User, username=request.POST['username'])

    org_name = request.POST.get('org', '').strip()
    existing_org = Organization.objects.filter(name__iexact=org_name).first()
    if existing_org:
        return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': existing_org.id}))
        # messages.add_message(request, messages.ERROR, "Organization '%s' already exists!" % org_name)
        # return HttpResponseRedirect(reverse('member_profile', kwargs={'username': user.username}))

    org = Organization.objects.create(name=org_name, lead=user, created_by=request.user)
    OrganizationMember.objects.create(organization=org, user=user, start_date=timezone.now(), admin=True)
    return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_edit(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        form = OrganizationForm(request.POST, request.FILES)
        form.public = request.POST['public']
        try:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))
    else:
        form = OrganizationForm(instance=org)

    context = {'organization': org, 'form':form,}
    return render(request, 'members/org_edit.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_member(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (not org.locked or request.user.is_staff or org.can_edit(request.user)):
        messages.add_message(request, messages.ERROR, "You do not have permission to add yourself to this organization")
        return HttpResponseRedirect(reverse('member_profile', kwargs={'username': request.username}))

    # We require a POST and we require an action
    if not request.method == "POST" or 'action' not in request.POST:
        return HttpResponseForbidden("Forbidden")
    action = request.POST['action']

    full_name = None
    org_member = None
    new_user = None
    new_username = request.POST.get('username', None)
    if new_username:
        new_user = User.objects.get(username=new_username)
        full_name = new_user.get_full_name()
        # print("user: %s" % full_name)
    member_id = request.POST.get('member_id', None)
    if member_id:
        org_member = org.organizationmember_set.get(id=member_id)
        full_name = org_member.user.get_full_name()
        # print("member: %s" % full_name)

    try:
        # form = OrganizationMemberForm()
        if 'edit' == action:
            form = OrganizationMemberForm(instance=org_member)
        if 'add' == action:
            initial_data={ 'username':new_username,
                'start_date': timezone.now()
            }

            form = OrganizationMemberForm(initial=initial_data)
        if 'save' == action:
            form = OrganizationMemberForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))
            else:
                print form
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))

    context = {'organization': org, 'member':org_member, 'username':new_username,
        'full_name':full_name, 'form':form, 'action':action,
    }
    return render(request, 'members/org_member.html', context)

@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_edit_photo(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        org.photo = request.FILES.get('photo', None)

        org.save();

        return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))

    else:
        form = OrganizationForm(request.POST, request.FILES)

    context = { 'organization': org }
    return render(request, 'members/org_edit_photo.html', context)


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
