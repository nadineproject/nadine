from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib import messages
from django.conf import settings

from nadine.models.membership import MembershipPackage
from nadine.utils import network


@staff_member_required
def index(request):
    ip = network.get_addr(request)
    context = {'settings':settings, 'ip': ip, 'request':request}
    return render(request, 'staff/settings/index.html', context)


@staff_member_required
def membership_packages(request):
    packages = MembershipPackage.objects.all().order_by('name')
    context = {'packages':packages}
    return render(request, 'staff/settings/membership_packages.html', context)

# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
