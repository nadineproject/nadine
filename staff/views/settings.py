from datetime import date, datetime
from slugify import slugify

from django.utils import timezone
from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.sites.models import Site
from django.forms.formsets import formset_factory
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.core.files.storage import FileSystemStorage

from nadine.models.membership import MembershipPackage, SubscriptionDefault
from nadine.models.profile import FileUpload
from nadine.models.resource import Resource, Room
from nadine.utils import network
from nadine.forms import HelpTextForm, MOTDForm, MembershipPackageForm, RoomForm
from nadine.settings import MOTD_TIMEOUT
from member.models import HelpText, MOTD


def times_timeszones(date):
    if not date:
        return None
    with_time = date + ' 00:00'
    time_dt = datetime.strptime(with_time, "%Y-%m-%d %H:%M")
    final = timezone.make_aware(time_dt, timezone.get_current_timezone())
    return final


@staff_member_required
def index(request):
    ip = network.get_addr(request)
    context = {'settings': settings, 'ip': ip, 'request': request}
    return render(request, 'staff/settings/index.html', context)


@staff_member_required
def membership_packages(request):
    packages = SubscriptionDefault.objects.all().order_by('package')
    PackageFormset = formset_factory(MembershipPackageForm)
    package = request.GET.get('package', None)
    sub_data = None
    enabled = False
    if package != None:
        pkg = MembershipPackage.objects.get(id=package)
        sub_defaults = SubscriptionDefault.objects.filter(package=pkg)
        sub_data = [{'name':pkg.name,'sub_id': s.id, 'package': pkg.id, 'enabled': pkg.enabled, 'resource': s.resource.id, 'allowance': s.allowance, 'monthly_rate': s.monthly_rate, 'overage_rate': s.overage_rate} for s in sub_defaults]
        enabled = pkg.enabled

    if request.method == 'POST':
        try:
            with transaction.atomic():
                package_formset = PackageFormset(request.POST)
                if package_formset.is_valid():
                    for p in package_formset:
                        if p.cleaned_data.get('name') != None:
                            if p.cleaned_data.get('monthly_rate') != None:
                                p.save()
                    messages.success(request, 'Successfully edited membership packages.')
                    return HttpResponseRedirect(reverse('staff:settings:membership_packages'))
                else:
                    print((package_formset.errors))
        except IntegrityError as e:
            print(('There was an ERROR: %s' % e.message))
            messages.error(request, 'There was an error creating the new membership package')
    else:
        package_formset = PackageFormset(initial=sub_data)
        package_form = MembershipPackageForm()
    context = {'packages':packages,
               'package': package,
               'package_formset': package_formset,
               'enabled': enabled,
               'package_form': package_form,
               }
    return render(request, 'staff/settings/membership_packages.html', context)


@staff_member_required
def helptexts(request):
    helps = HelpText.objects.all()
    if helps:
        latest = HelpText.objects.filter().order_by('-order')[0]
        latest_order = latest.order + 1
    else:
        latest = None
        latest_order = 0
    selected = None
    message = None
    selected_help = request.GET.get('selected_help', None)
    if selected_help:
        selected = HelpText.objects.get(title=selected_help)

    if request.method == "POST":
        to_update = request.POST.get('id', None)
        if to_update:
            updated = HelpText.objects.get(id=to_update)
            updated.title = request.POST['title']
            slug = request.POST['slug']
            updated.slug = slugify(slug)
            updated.template = request.POST['template']
            updated.save()

            return HttpResponseRedirect(reverse('staff:tasks:todo'))

        else:
            helptext_form = HelpTextForm(request.POST)
            slug = slugify(request.POST['slug'])
            title = request.POST['title']
            template = request.POST['template']
            order = request.POST['order']
            helptext_form = HelpText(title=title, template=template, slug=slug, order=order)
            helptext_form.save()

            return HttpResponseRedirect(reverse('staff:tasks:todo'))
    else:
        helptext_form = HelpTextForm()

    context = {'latest_order': latest_order, 'helps': helps, 'helptext_form': helptext_form, 'selected': selected, 'message': message}
    return render(request, 'staff/settings/helptexts.html', context)


@staff_member_required
def motd(request):
    prev_motd = MOTD.objects.filter().order_by('-end_ts')
    selected = None
    message = None
    delay = settings.MOTD_TIMEOUT
    selected_motd = request.GET.get('selected_motd', None)
    if selected_motd:
        selected = MOTD.objects.get(id=selected_motd)

    if request.method == 'POST':
        to_update = request.POST.get('id', None)
        start_ts = times_timeszones(request.POST.get('start_ts'))
        end_ts = times_timeszones(request.POST.get('end_ts'))

        if to_update:
            updated = MOTD.objects.get(id=to_update)
            updated.message = request.POST['message']
            updated.save()
            return HttpResponseRedirect(reverse('staff:tasks:todo'))
        else:
            motd_form = MOTDForm(request.POST)

            if MOTD.objects.filter(start_ts__lte=start_ts, end_ts__gte=end_ts):
                message = 'A Message of the Day exists for this time period'

            else:
                motd_form.start_ts = start_ts
                motd_form.end_ts = end_ts
                motd_form.message = request.POST['message']
                if motd_form.is_valid():
                    motd_form.save()
                    return HttpResponseRedirect(reverse('staff:tasks:todo'))
    else:
        motd_form = MOTDForm()
    context = {'prev_motd': prev_motd,
               'motd_form': motd_form,
               'delay': delay,
               'selected': selected,
               'message': message}
    return render(request, 'staff/settings/motd.html', context)


# TODO - Not quite ready yet --JLS
# @staff_member_required
# def document_upload(request):
#     doc_form = DocUploadForm()
#     # To be used to preview uploaded docs
#     # docs = FileUpload.objects.values_list('document_type', flat=True).distinct().exclude(document_type='None')
#     docs = Documents.objects.values_list('name', flat=True).distinct().exclude(name='None')
#
#     if request.method == 'POST':
#         if 'doc_type' in request.POST:
#             user = request.user
#             today = localtime(now()).date()
#             doc_type = request.POST.get('doc_type')
#             pdf_args = {'doc_type': doc_type}
#             return render(request, 'staff/settings/doc_preview.html', pdf_args)
#         else:
#             doc_form = DocUploadForm(request.POST, request.FILES)
#             # name = slugify(request.POST.get('name'))
#             # doc = request.POST.get('document')
#             if doc_form.is_valid():
#                 doc_form.save()
#                 messages.success(request, 'Successfully uploaded new document.')
#                 return HttpResponseRedirect(reverse('staff:settings:doc_upload'))
#             else:
#                 print(doc_form.errors)
#                 messages.error(request, 'There was an error uploading your document')
#     context = {
#         'doc_form': doc_form,
#         'docs': docs,
#     }
#     return render(request, 'staff/settings/doc_upload.html', context)

@staff_member_required
def edit_rooms(request):
    rooms = Room.objects.all().order_by('floor')
    room = request.GET.get('room', None)
    rm_data = None
    if room != None:
        rm = Room.objects.get(id=room)
        rm_data = {'room_id': rm.id, 'name': rm.name, 'floor': rm.floor, 'seats':rm.seats, 'description':rm.description, 'max_capacity':rm.max_capacity, 'default_rate':rm.default_rate, 'location': rm.location, 'has_av':rm.has_av, 'has_phone': rm.has_phone, 'image':rm.image, 'members_only':rm.members_only}

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('staff:tasks:todo'))
        else:
            messages.error(request, 'There was an error updating meeting rooms.')
    else:
        form = RoomForm(initial=rm_data)
    context = { 'rooms': rooms,
                'form': form,
                'room': room,
              }
    return render(request, 'staff/settings/edit_rooms.html', context)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
