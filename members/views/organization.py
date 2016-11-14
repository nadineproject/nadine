from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

#from nadine.models.core import UserProfile, Membership
from nadine.models.organization import Organization, OrganizationMember

from members.views.core import is_active_member


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def view_organization(request, id):
    org = get_object_or_404(Organization, id=id)
    if not org.can_edit(request.user) and not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    context = {'organization': org}
    return render(request, 'members/organization.html', context)


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
