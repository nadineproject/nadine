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

from nadine.forms import OrganizationForm, OrganizationMemberForm
from nadine.models.organization import Organization, OrganizationMember

from members.views.core import is_active_member


@login_required
def org_list(request):
    orgs = Organization.objects.active_organizations()
    context = {'organizations': orgs}
    return render(request, 'members/org_list.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_view(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    can_edit = org.can_edit(request.user) or request.user.is_staff

    # Individual forms for each of the organization members
    # org_forms = []
    # for m in org.organizationmember_set.all().order_by('start_date'):
    #     form = OrganizationMemberForm(instance=m)
    #     org_forms.append((m, form))
    members = org.organizationmember_set.all().order_by('start_date')

    context = {'organization': org, 'can_edit':can_edit,
        # 'org_forms':org_forms,
        'members':members,
    }
    return render(request, 'members/org_view.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_edit(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        form = OrganizationForm(request.POST, request.FILES)
        public = request.POST.get('public', False)
        if public == 'True':
            form.public = True
        else:
            form.public = False
        try:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))
            else:
                print form
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
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    # We require a POST and we require an action
    if not request.method == "POST" or 'action' not in request.POST:
        return HttpResponseForbidden("Forbidden")
    action = request.POST['action']

    org_member = None
    if 'member_id' in request.POST:
        member_id = request.POST['member_id']
        org_member = org.organizationmember_set.get(id=member_id)

    form = OrganizationMemberForm()
    if 'edit' == action:
        try:
            form = OrganizationMemberForm(instance=org_member)
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not get member: %s" % str(e))
    if 'save' == action:
        form = OrganizationMemberForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not save: %s" % str(e))

    context = {'organization': org, 'member':org_member,
        'form':form, 'action':action
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

@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def org_tags(request, org_id):
    error = None
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    org_tags = org.tags.all()
    if request.method == 'POST':
        tag = request.POST.get('tag')
        if tag:
            for p in string.punctuation:
                if p in tag:
                    error = "Tags can't contain punctuation."
                    break
            else:
                org.tags.add(tag.lower())
        return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))

    all_tags = Organization.tags.all()
    context = {'organization': org, 'org_tags': org_tags, 'all_tags': all_tags,
        'error': error, 'settings': settings}
    return render(request, 'members/org_tags.html', context)


@login_required
def org_remove_tag(request, org_id, tag):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))
    org.tags.remove(tag)
    return HttpResponseRedirect(reverse('member_org_view', kwargs={'org_id': org.id}))


@csrf_exempt
@login_required
def org_search_json(request):
    items = []
    term = request.GET.get('term', '').strip()
    query = Organization.objects.all()
    if len(term) >= 3:
        query = query.filter(name__icontains=term)
    elif len(term) > 0:
        query = query.filter(name__istartswith=term)
    for i in query.order_by('name'):
        items.append({'id': i.id, 'value': i.name,})
    return JsonResponse(items, safe=False)


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
