from datetime import date, datetime

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
from django.utils import timezone

from nadine.utils import network
from nadine.forms import HelpTextForm, MOTDForm
from nadine.settings import MOTD_TIMEOUT
from members.models import HelpText, MOTD


@staff_member_required
def index(request):
    ip = network.get_addr(request)
    context = {'settings':settings, 'ip': ip, 'request':request}
    return render(request, 'staff/settings/index.html', context)


@staff_member_required
def helptexts(request):
    helps = HelpText.objects.all()
    latest = HelpText.objects.filter().order_by('-order')[0]
    latest_order = latest.order + 1
    selected = None
    selected_help = request.GET.get('selected_help', None)
    if selected_help:
        selected = HelpText.objects.get(title=selected_help)

    if request.method == "POST":
        to_update = request.POST.get('id', None)
        if to_update:
            updated = HelpText.objects.get(id=to_update)
            updated.title = request.POST['title']
            slug = request.POST['slug'].strip()
            updated.slug = slug.replace(" ", "_")
            updated.template = request.POST['template']
            updated.save()

            return HttpResponseRedirect(reverse('staff:settings:index'))
        else:
            helptext_form = HelpTextForm(request.POST)
            helptext_form.slug = helptext_form.slug.strip().replace(" ", "_")
            if helptext_form.is_valid():
                helptext_form.save()
                return HttpResponseRedirect(reverse('staff:settings:index'))
    else:
        helptext_form = HelpTextForm()

    context = {'latest_order': latest_order, 'helps': helps, 'helptext_form': helptext_form, 'selected': selected}
    return render(request, 'staff/settings/helptexts.html', context)

@staff_member_required
def motd(request):
    prev_motd = MOTD.objects.filter().order_by('-end_ts')
    delay = settings.MOTD_TIMEOUT
    if request.method == 'POST':
        motd_form = MOTDForm(request.POST)

        start_ts = request.POST.get('start_ts') + ' 00:00'
        end_ts = request.POST.get('end_ts') + ' 00:00'
        start_dt = datetime.strptime(start_ts, "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(end_ts, "%Y-%m-%d %H:%M")
        motd_form.start_ts = timezone.make_aware(start_dt, timezone.get_current_timezone())
        motd_form.end_ts = timezone.make_aware(end_dt, timezone.get_current_timezone())

        if motd_form.is_valid():
            motd_form.save()

            return HttpResponseRedirect(reverse('staff:settings:index'))
    else:
        motd_form = MOTDForm()

    context = {'prev_motd': prev_motd, 'motd_form': motd_form, 'delay': delay}
    return render(request, 'staff/settings/motd.html', context)
