import string

from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms.formsets import formset_factory
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from nadine.forms import OrganizationForm, OrganizationMemberForm, ProfileImageForm, OrganizationSearchForm, LinkForm, BaseLinkFormSet
from nadine.models.organization import Organization, OrganizationMember

from member.views.core import is_active_member


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_list(request):
    orgs = Organization.objects.active_organizations()

    search_terms = None
    search_results = None
    if request.method == "POST":
        search_form = OrganizationSearchForm(request.POST)
        if search_form.is_valid():
            search_terms = search_form.cleaned_data['terms']
            search_results = Organization.objects.search(search_terms)
            if len(search_results) == 1:
                return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': search_results[0].id}))
    else:
        search_form = OrganizationSearchForm()

    context = {'organizations': orgs,
               'search_results': search_results,
               'search_form': search_form,
               'search_terms': search_terms,
               }
    return render(request, 'member/organization/org_list.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_view(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    can_edit = org.can_edit(request.user) or request.user.is_staff

    members = org.organizationmember_set.all().order_by('start_date')
    counts = {'total': members.count(), 'active': 0, 'inactive': 0}
    for m in members:
        if m.is_active():
            counts['active'] = counts['active'] + 1
        else:
            counts['inactive'] = counts['inactive'] + 1

    show_all = 'show_all' in request.GET or counts['active'] == 0
    context = {'organization': org,
               'can_edit': can_edit,
               'members': members,
               'counts': counts,
               'show_all': show_all,
               }
    return render(request, 'member/organization/org_view.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_add(request):
    if 'org' not in request.POST and 'username' in request.POST:
        return HttpResponseForbidden("Forbidden")

    user = get_object_or_404(User, username=request.POST['username'])

    org_name = request.POST.get('org', '').strip()
    existing_org = Organization.objects.filter(name__iexact=org_name).first()
    if existing_org:
        return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': existing_org.id}))
        # messages.add_message(request, messages.ERROR, "Organization '%s' already exists!" % org_name)
        # return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))

    org = Organization.objects.create(name=org_name, lead=user, created_by=request.user)
    OrganizationMember.objects.create(organization=org, user=user, start_date=timezone.now(), admin=True)
    return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_edit(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    OrgFormSet = formset_factory(LinkForm, formset=BaseLinkFormSet)

    org_links = org.websites.all()
    link_data = [{'url_type': l.url_type, 'url': l.url, 'org_id': org.id} for l in org_links]

    if request.method == "POST":
        form = OrganizationForm(request.POST, request.FILES)
        org_link_formset = OrgFormSet(request.POST)
        form.public = request.POST['public']
        try:
            if form.is_valid():
                if org_link_formset.is_valid():
                    for link in link_data:
                        del_url = link.get('url')
                        org.websites.filter(url=del_url).delete()
                    for link_form in org_link_formset:
                        if not link_form.cleaned_data.get('org_id'):
                            link_form.cleaned_data['org_id'] = org.id
                        try:
                            if link_form.is_valid():
                                url_type = link_form.cleaned_data.get('url_type')
                                url = link_form.cleaned_data.get('url')

                                if url_type and url:
                                    link_form.save()
                        except Exception as e:
                            print(("Could not save website: %s" % str(e)))

                    form.save()
                    return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))
                else:
                    messages.error(request, 'Please make sure the websites have a valid URL and URL type.')
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))
    else:
        form = OrganizationForm(instance=org)
        org_link_formset = OrgFormSet(initial=link_data)

    context = {'organization': org,
               'form': form,
               'org_link_formset': org_link_formset,
               }
    return render(request, 'member/organization/org_edit.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_member(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (not org.locked or request.user.is_staff or org.can_edit(request.user)):
        messages.add_message(request, messages.ERROR, "You do not have permission to add yourself to this organization")
        return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': request.username}))

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
            initial_data = {'username': new_username,
                            'start_date': timezone.now()
                            }

            form = OrganizationMemberForm(initial=initial_data)
        if 'save' == action:
            form = OrganizationMemberForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))
            else:
                print(form)
    except Exception as e:
        messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))

    context = {'organization': org,
               'member': org_member,
               'username': new_username,
               'full_name': full_name,
               'form': form,
               'action': action,
               }
    return render(request, 'member/organization/org_member.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def org_edit_photo(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))
            else:
                print(form)
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))
    else:
        form = ProfileImageForm()

    context = {
        'organization': org,
        'form': form,
    }
    return render(request, 'member/profile/profile_image_edit.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
