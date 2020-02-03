from datetime import date, datetime, timedelta

from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.sites.models import Site
from django.contrib import messages
from django.conf import settings

from nadine.models.alerts import MemberAlert

@staff_member_required
def todo(request):
    member_alerts = []
    for key, desc in MemberAlert.ALERT_DESCRIPTIONS:
        count = MemberAlert.objects.unresolved(key).count()
        member_alerts.append((key, desc, count))

    showall = "showall" in request.GET

    if showall:
        assigned_alerts = MemberAlert.objects.filter(resolved_ts__isnull=True, muted_ts__isnull=True, assigned_to__isnull=False)
    else:
        assigned_alerts = request.user.assigned_alerts.filter(resolved_ts__isnull=True, muted_ts__isnull=True)

    # Did anyone forget to sign in in the last 7 days?
    check_date = timezone.now().date() - timedelta(days=7)
    not_signed_in = User.helper.not_signed_in_since(check_date)
    staff_members = User.objects.filter(is_staff=True).order_by('id').reverse()
    today = timezone.now().date()

    context = {
        'member_alerts': member_alerts,
        'assigned_alerts': assigned_alerts,
        'not_signed_in': not_signed_in,
        'staff_members': staff_members,
        'showall':showall,
        'today':today
    }
    return render(request, 'staff/tasks/todo.html', context)


@staff_member_required
def detail(request, key):
    if request.method == 'POST' and "action" in request.POST:
        action = request.POST.get("action").lower()
        try:
            alert = get_object_or_404(MemberAlert, pk=request.POST.get("alert_id"))
            note = request.POST.get("note", "").strip()
            alert.note = note
            assigned_to = request.POST.get("assigned_to", "")
            if assigned_to:
                alert.assigned_to = User.objects.get(username=assigned_to)
            else:
                alert.assigned_to = None

            if action == "mute" and not note:
                messages.add_message(request, messages.ERROR, "Note required to mute an alert!")
            else:
                if action == "mute":
                    alert.muted_ts = timezone.now()
                    alert.muted_by = request.user
                elif action == "resolve":
                    alert.resolved_ts = timezone.now()
                    alert.resolved_by = request.user
                alert.save()
                messages.add_message(request, messages.INFO, "Alert '%s:%s' %sd!" % (alert.user.username, alert.key, action))
        except Exception as e:
            messages.add_message(request, messages.ERROR, "Could not %s alert: %s" % (action, e))

        if "next" in request.POST:
            next_url = request.POST.get("next")
            return HttpResponseRedirect(next_url)

    alerts = MemberAlert.objects.unresolved(key).order_by('user__first_name')
    description = MemberAlert.getDescription(key)
    is_system_alert = MemberAlert.isSystemAlert(key)
    staff_members = User.objects.filter(is_staff=True).order_by('id').reverse()

    context = {
        'key': key,
        'description': description,
        'alerts': alerts,
        'is_system_alert': is_system_alert,
        'staff_members': staff_members,
    }
    return render(request, 'staff/tasks/detail.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
