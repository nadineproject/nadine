from django.template import RequestContext
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect

from comlink.models import MailingList, EmailMessage


@staff_member_required
def home(request):
    lists = MailingList.objects.all()
    return render(request, 'staff/mailing_lists/home.html', {'lists': lists})


@staff_member_required
def list_messages(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    messages = mailing_list.emailmessage_set.all().order_by('-received')[0:15]
    context = {
        'mailing_list': mailing_list,
        'messages': messages,
    }
    return render(request, 'staff/mailing_lists/messages.html', context)


@staff_member_required
def list_subscribers(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    not_subscribed = User.helper.active_members().exclude(id__in=mailing_list.subscribed()).order_by('first_name', 'last_name')
    context = {'mailing_list': mailing_list, 'not_subscribed': not_subscribed}
    return render(request, 'staff/mailing_lists/subscribers.html', context)


@login_required
def subscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.subscribe(user)
        return HttpResponseRedirect(reverse('staff:mailing_lists:subscribers', args=[list_id]))
    return render(request, 'staff/mailing_lists/subscribe.html', {'user': user, 'mailing_list': mailing_list})


@login_required
def unsubscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.unsubscribe(user)
        return HttpResponseRedirect(reverse('staff:mailing_lists:subscribers', args=[list_id]))
    return render(request, 'staff/mailing_lists/unsubscribe.html', {'user': user, 'mailing_list': mailing_list})


@staff_member_required
def moderator_list(request):
    return render(request, 'staff/mailing_lists/moderator_list.html', {})


@staff_member_required
def moderator_inspect(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    return render(request, 'staff/mailing_lists/moderator_inspect.html', {'incoming_mail': incoming_mail})


@staff_member_required
def moderator_approve(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation:', incoming_mail, incoming_mail.state)
        return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))
    #print('accepting')
    incoming_mail.create_outgoing()
    return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))


@staff_member_required
def moderator_reject(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation.')
        return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))

    incoming_mail.reject()
    return HttpResponseRedirect(reverse('staff:mailing_lists:moderate'))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
