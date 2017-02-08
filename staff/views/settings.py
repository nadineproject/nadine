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

from nadine.utils import network
from nadine.forms import HelpTextForm
from members.models import HelpText


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
        # Check to see if existing help text and update it or make new one
        to_update = request.POST.get('id', None)
        if to_update:
            updated = HelpText.objects.get(id=to_update)
            updated.title = request.POST['title']
            updated.slug = request.POST['slug']
            updated.template = request.POST['template']
            updated.save()

            return HttpResponseRedirect(reverse('staff:settings:index'))
        else:
            helptext_form = HelpTextForm(request.POST)
            if helptext_form.is_valid():
                helptext_form.save()
                return HttpResponseRedirect(reverse('staff:settings:index'))
    else:
        helptext_form = HelpTextForm()

    context = {'latest_order': latest_order, 'helps': helps, 'helptext_form': helptext_form, 'selected': selected}
    return render(request, 'staff/settings/helptexts.html', context)
