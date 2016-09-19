from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect

from interlink.models import MailingList, IncomingMail


@staff_member_required
def index(request):
    lists = MailingList.objects.all()
    return render_to_response('interlink/index.html', {'lists': lists}, context_instance=RequestContext(request))


@staff_member_required
def list_messages(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    return render_to_response('interlink/messages.html', {'mailing_list': mailing_list}, context_instance=RequestContext(request))


@staff_member_required
def list_subscribers(request, list_id):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    not_subscribed = User.helper.active_members().exclude(id__in=mailing_list.subscribers.all())
    return render_to_response('interlink/subscribers.html', {'mailing_list': mailing_list, 'not_subscribed': not_subscribed}, context_instance=RequestContext(request))


@login_required
def subscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.subscribers.add(user)
        return HttpResponseRedirect(reverse('interlink_subscribers', args=[list_id]))
    return render_to_response('interlink/subscribe.html', {'user': user, 'mailing_list': mailing_list}, context_instance=RequestContext(request))


@login_required
def unsubscribe(request, list_id, username):
    mailing_list = get_object_or_404(MailingList, pk=list_id)
    user = get_object_or_404(User, username=username)
    if request.method == 'POST':
        if request.POST.get('confirm', 'No') == "Yes":
            mailing_list.subscribers.remove(user)
        return HttpResponseRedirect(reverse('interlink_subscribers', args=[list_id]))
    return render_to_response('interlink/unsubscribe.html', {'user': user, 'mailing_list': mailing_list}, context_instance=RequestContext(request))


@staff_member_required
def moderator_list(request):
    return render_to_response('interlink/moderator_list.html', {}, context_instance=RequestContext(request))


@staff_member_required
def moderator_inspect(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    return render_to_response('interlink/moderator_inspect.html', {'incoming_mail': incoming_mail}, context_instance=RequestContext(request))


@staff_member_required
def moderator_approve(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('interlink_moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation:', incoming_mail, incoming_mail.state)
        return HttpResponseRedirect(reverse('interlink_moderate'))
    #print('accepting')
    incoming_mail.create_outgoing()
    return HttpResponseRedirect(reverse('interlink_moderate'))


@staff_member_required
def moderator_reject(request, id):
    incoming_mail = get_object_or_404(IncomingMail, pk=id)
    if not request.user in incoming_mail.mailing_list.moderators.all():
        #print(request.user.get_full_name(), 'tried to moderate an email for %s' % incoming_mail.mailing_list.name)
        return HttpResponseRedirect(reverse('interlink_moderate'))

    if incoming_mail.state != 'moderate':
        #print('Tried to moderate an email which needs no moderation.')
        return HttpResponseRedirect(reverse('interlink_moderate'))

    incoming_mail.reject()
    return HttpResponseRedirect(reverse('interlink_moderate'))


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
