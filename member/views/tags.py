import string
import traceback
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from nadine.models.profile import UserProfile
from nadine.models.organization import Organization

from member.views.core import is_active_member


def get_tag_data(type):
    tags = []
    if type == "members":
        for tag in UserProfile.tags.all().order_by('name'):
            items = User.helper.members_with_tag(tag)
            count = items.count()
            if count:
                tags.append((tag, items, count))
    elif type == "organizations":
        for tag in Organization.tags.all().order_by('name'):
            items = Organization.objects.with_tag(tag)
            count = items.count()
            if count:
                tags.append((tag, items, count))
    else:
        raise Exception("Invalid type '%s'" % type)
    return tags


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def tag_list(request, type):
    tags = get_tag_data(type)
    context = {'type': type, 'tags': tags}
    return render(request, 'member/tags/tag_list.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def tag_cloud(request, type):
    tags = get_tag_data(type)
    context = {'type': type, 'tags': tags}
    return render(request, 'member/tags/tag_cloud.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def tag_view(request, type, tag):
    context = {'type': type, 'tag': tag}
    if type == "members":
        context['members'] = User.helper.members_with_tag(tag)
    elif type == "organizations":
        context['organizations'] = Organization.objects.with_tag(tag)
    else:
        return Http404()
    return render(request, 'member/tags/tag_view.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def add_tag(request, username):
    user = get_object_or_404(User, username=username)
    if not user == request.user and not request.user.is_staff:
        return HttpResponseForbidden

    tag = request.POST.get("tag", "").strip().lower()
    if tag.isalnum() or ' ' in tag or '-' in tag:
        user.profile.tags.add(tag)
    else:
        messages.add_message(request, messages.ERROR, "Tags can't contain punctuation.")
    return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': user.username}))


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def remove_tag(request, username, tag):
    user = get_object_or_404(User, username=username)
    if not user == request.user and not request.user.is_staff:
        return HttpResponseForbidden
    user.profile.tags.remove(tag)
    return HttpResponseRedirect(reverse('member:profile:view', kwargs={'username': username}))


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def add_org_tag(request, org_id):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseForbidden("Forbidden")

    tag = request.POST.get("tag", "").strip().lower()
    if tag.isalnum() or ' ' in tag or '-' in tag:
        org.tags.add(tag)
    else:
        messages.add_message(request, messages.ERROR, "Tags can't contain punctuation.")
    return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))


@login_required
@user_passes_test(is_active_member, login_url='member:not_active')
def remove_org_tag(request, org_id, tag):
    org = get_object_or_404(Organization, id=org_id)
    if not (request.user.is_staff or org.can_edit(request.user)):
        return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))
    org.tags.remove(tag)
    return HttpResponseRedirect(reverse('member:org:view', kwargs={'org_id': org.id}))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
