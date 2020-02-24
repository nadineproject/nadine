from datetime import date, datetime, timedelta

from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest, JsonResponse

from nadine.models.profile import UserProfile
from nadine.models.organization import Organization

from member.views.core import is_active_member

######################################################################
# Helper Functions
######################################################################


def query_to_item_list(query):
    items = []
    for i in query.order_by('name'):
        items.append({'id': i.id, 'value': i.name, })
    return items


def filter_query(query, term):
    if len(term) >= 3:
        query = query.filter(name__icontains=term)
    elif len(term) > 0:
        query = query.filter(name__istartswith=term)
    return query


######################################################################
# Views
######################################################################

# TODO - These should be class views. --JLS

@login_required
@user_passes_test(is_active_member, login_url='/404.html')
def user_tags(request):
    term = request.GET.get('term', '').strip()
    query = UserProfile.tags.all()
    query = filter_query(query, term)
    items = query_to_item_list(query)
    return JsonResponse(items, safe=False)


@login_required
@user_passes_test(is_active_member, login_url='/404.html')
def org_tags(request):
    term = request.GET.get('term', '').strip()
    query = Organization.tags.all()
    query = filter_query(query, term)
    items = query_to_item_list(query)
    return JsonResponse(items, safe=False)


@login_required
@user_passes_test(is_active_member, login_url='/404.html')
def org_search(request):
    term = request.GET.get('term', '').strip()
    query = Organization.objects.all()
    query = filter_query(query, term)
    items = query_to_item_list(query)
    return JsonResponse(items, safe=False)


@login_required
@user_passes_test(is_active_member, login_url='/404.html')
def user_search(request):
    term = request.GET.get('term', '').strip()
    query = User.objects.all()
    if len(term) >= 3:
        if ' ' in term:
            terms = term.split(' ')
            first = Q(first_name__icontains=terms[0])
            last = Q(last_name__icontains=terms[1])
            query = query.filter(first & last)
        else:
            first = Q(first_name__icontains=term)
            last = Q(last_name__icontains=term)
            query = query.filter(first | last)
    elif len(term) > 0:
        query = query.filter(first_name__istartswith=term)
    items = []
    for i in query.order_by('first_name'):
        items.append({'id': i.id,
                      'label': i.get_full_name(),
                      'value': i.username,
                      })
    return JsonResponse(items, safe=False)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
