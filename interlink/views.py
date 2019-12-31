from django.template import RequestContext
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect

from interlink.models import MailingList, IncomingMail


@staff_member_required
def home(request):
    lists = MailingList.objects.all()
    return render(request, 'interlink/home.html', {'lists': lists})


@staff_member_required
def list_messages(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    incoming_messages = mailing_list.incoming_mails.all().order_by('-sent_time')[0:15]
    outgoing_messages = mailing_list.outgoing_mails.all().order_by('-sent')[0:15]
    context = {
        'mailing_list': mailing_list,
        'incoming_messages': incoming_messages,
        'outgoing_messages': outgoing_messages,
    }
    return render(request, 'interlink/messages.html', context)


@staff_member_required
def list_subscribers(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    not_subscribed = User.helper.active_members().exclude(id__in=mailing_list.subscribed())
    context = {'mailing_list': mailing_list, 'not_subscribed': not_subscribed}
    return render(request, 'interlink/subscribers.html', context)


@login_required
def subscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.subscribe(user)
        return HttpResponseRedirect(reverse('interlink:subscribers', args=[list_id]))
    return render(request, 'interlink/subscribe.html', {'user': user, 'mailing_list': mailing_list})


@login_required
def unsubscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.unsubscribe(user)
        return HttpResponseRedirect(reverse('interlink:subscribers', args=[list_id]))
    return render(request, 'interlink/unsubscribe.html', {'user': user, 'mailing_list': mailing_list})


@staff_member_required
def moderator_list(request):
    return render(request, 'interlink/moderator_list.html', {})


@staff_member_required
def moderator_inspect(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    return render(request, 'interlink/moderator_inspect.html', {'incoming_mail': incoming_mail})


@staff_member_required
def moderator_approve(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('interlink:moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation:', incoming_mail, incoming_mail.state)
        return HttpResponseRedirect(reverse('interlink:moderate'))
    #print('accepting')
    incoming_mail.create_outgoing()
    return HttpResponseRedirect(reverse('interlink:moderate'))


@staff_member_required
def moderator_reject(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('interlink:moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation.')
        return HttpResponseRedirect(reverse('interlink:moderate'))

    incoming_mail.reject()
    return HttpResponseRedirect(reverse('interlink:moderate'))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
