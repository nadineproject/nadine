from datetime import datetime, timedelta, date

from django.contrib import auth
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.timezone import localtime, now, make_aware, get_current_timezone

from arpwatch.forms import *
from arpwatch.models import *
from arpwatch import arp


@staff_member_required
def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Check the upload logs to make sure we haven't already loaded this file
            if (UploadLog.objects.filter(file_name=file.name).count() > 0):
                raise Exception('File Already Loaded')
            if request.user.is_authenticated():
                UploadLog.objects.create(user=request.user, file_name=file.name, file_size=file.size)
            else:
                UploadLog.objects.create(file_name=file.name, file_size=file.size)
            arp.import_file(file)
            # return HttpResponseRedirect('/success/url/')
    else:
        form = UploadFileForm()
    return render(request, 'arpwatch/home.html', {'form': form})


def import_files(request):
    page_message = "success"
    try:
        arp.import_all()
    except RuntimeError as err:
        page_message = err

    return render(request, 'arpwatch/import.html', {'page_message': page_message})


@staff_member_required
def device_list(request):
    devices = UserDevice.objects.filter(ignore=False)
    return render(request, 'arpwatch/device_list.html', {'devices': devices})


@staff_member_required
def device(request, device_id):
    device = UserDevice.objects.get(pk=device_id)
    logs = ArpLog.objects.for_device(device_id)
    return render(request, 'arpwatch/device_view.html', {'device': device, 'logs': logs})


@staff_member_required
def device_logs_today(request):
    today = localtime(now())
    return device_logs_by_day(request, str(today.year), str(today.month), str(today.day))


@staff_member_required
def device_logs_by_day(request, year, month, day):
    log_date = date(year=int(year), month=int(month), day=int(day))
    start = datetime(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0, microsecond=0)
    start = make_aware(start, get_current_timezone())
    end = start + timedelta(days=1)
    device_logs = ArpLog.objects.for_range(start, end)
    context = {'device_logs': device_logs, 'day': log_date,
        'next_day': log_date + timedelta(days=1),
        'previous_day': log_date - timedelta(days=1)}
    return render(request, 'arpwatch/device_logs.html', context)


@staff_member_required
def logins_today(request):
    today = localtime(now())
    return logins_by_day(request, str(today.year), str(today.month), str(today.day))


def logins_by_day(request, year, month, day):
    log_date = date(year=int(year), month=int(month), day=int(day))
    start = datetime(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0, microsecond=0)
    start = make_aware(start, get_current_timezone())
    end = start + timedelta(days=1)
    logs = UserRemoteAddr.objects.filter(logintime__gt=start, logintime__lt=end)
    context = {'logs': logs, 'day': log_date,
        'next_day': log_date + timedelta(days=1),
        'previous_day': log_date - timedelta(days=1)}
    return render(request, 'arpwatch/user_logins.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
