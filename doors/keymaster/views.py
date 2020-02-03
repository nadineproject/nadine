import time
import logging
import pytz
import traceback
from datetime import datetime, timedelta, date

from django.conf import settings
from django.template import RequestContext
from django.template import Context, loader
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now

from doors.keymaster.models import Keymaster, Door, DoorCode, DoorEvent
from doors.core import EncryptedConnection, Messages, DoorEventTypes
from nadine.utils import network
from nadine import email
from nadine.settings import TIME_ZONE

logger = logging.getLogger(__name__)


@staff_member_required
def home(request):
    keymasters = Keymaster.objects.filter(is_enabled=True)
    twoMinutesAgo = localtime(now()) - timedelta(minutes=2)
    logs = DoorEvent.objects.all().order_by('timestamp').reverse()[:11]

    if 'keymaster_id' in request.POST:
        km = get_object_or_404(Keymaster, id=request.POST.get('keymaster_id'))
        if request.POST.get('action') == "Force Sync":
            km.force_sync()
        elif 'action' in request.POST and "Clear" in request.POST.get('action'):
            km.clear_logs(log_id=request.POST.get('log_id', None))

    context = {'keymasters': keymasters, 'twoMinutesAgo': twoMinutesAgo,
         'event_logs': logs}
    return render(request, 'keymaster/home.html', context)


@staff_member_required
def logs(request):
    logs = DoorEvent.objects.all().order_by("timestamp").reverse()
    if 'username' in request.GET:
        username = request.GET.get('username')
        user = get_object_or_404(User, username=username)
        logs = logs.filter(user=user)
    if 'code' in request.GET:
        logs = logs.filter(code=request.GET.get('code'))
    if 'type' in request.GET:
        logs = logs.filter(event_type=request.GET.get('type'))
    if 'door' in request.GET:
        logs = logs.filter(door=request.GET.get('door'))

    limit = 100
    if 'limit' in request.GET:
        limit = int(request.GET.get('limit'))
    logs = logs[:limit]

    return render(request, 'keymaster/logs.html', {'event_logs':logs})


@staff_member_required
def user_keys(request, username):
    user = get_object_or_404(User, username=username)
    keys = DoorCode.objects.filter(user=user)
    logs = DoorEvent.objects.filter(user=user).order_by("timestamp").reverse()

    tenMinutesAgo = localtime(now()) - timedelta(minutes=10)
    potential_key = DoorEvent.objects.filter(timestamp__gte=tenMinutesAgo, event_type=DoorEventTypes.UNRECOGNIZED).order_by("timestamp").reverse().first()

    if 'code_id' in request.POST and request.POST.get('action') == "Delete":
        door_code = get_object_or_404(DoorCode, id=request.POST.get('code_id'))
        door_code.delete()

    if not 'view_all_logs' in request.GET:
        logs = logs[:10]

    context = {'user':user, 'keys':keys, 'logs':logs, 'potential_key':potential_key}
    return render(request, 'keymaster/user_keys.html', context)


@staff_member_required
def user_list(request):
    order_by = request.GET.get("order_by", "user__username")
    codes = DoorCode.objects.all().order_by(order_by)
    return render(request, 'keymaster/user_list.html', {'codes':codes})


@staff_member_required
def add_key(request):
    username = request.POST.get("username", "")
    code = request.POST.get("code", "")

    # Try and find one and only one user for this username
    user = None
    if username:
        user_search = User.objects.filter(username=username)
        if not user_search:
            messages.add_message(request, messages.ERROR, "Could not find user for username '%s'" % username)
        elif user_search.count() > 1:
            messages.add_message(request, messages.ERROR, "More then one user found for username '%s'" % username)
        else:
            user = user_search.first()

    # Make sure this door code isn't used by anyone else
    if code:
        if DoorCode.objects.filter(code=code).count() > 0:
            messages.add_message(request, messages.ERROR, "Door code '%s' already in use!" % code)
            code = ""

    # If we have enough information construct a door_code
    # but don't save it until we get user confirmation
    door_code = None
    if user and code:
        door_code = DoorCode(created_by=request.user, user=user, code=code)

    # Save the code if we've received user confirmation
    if door_code and 'add_door_code' in request.POST:
        door_code.save()
        email.announce_new_key(user)
        return HttpResponseRedirect(reverse('doors:keys', kwargs={'username': user.username}))

    # Pull a list of active members for our autocomplete
    active_members = User.helper.active_members()

    context = {'username':username, 'code':code, 'door_code':door_code, 'active_members':active_members}
    return render(request, 'keymaster/add_key.html', context)


@staff_member_required
def test_door(request):
    ip_address = request.POST.get("ip_address", "")
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    xml_request = request.POST.get("xml_request", "")
    xml_response = ""
    if len(xml_request) > 0:
        start_ts = localtime(now())
        controller = DoorController(ip_address, username, password)
        response_code, xml_response = controller.__send_xml_str(xml_request)
        response_time = localtime(now()) - start_ts
        print(("response code: %d, response time: %s" % (response_code, response_time)))
    else:
        # Start with the basic framework
        xml_request = '<?xml version="1.0" encoding="UTF-8"?>\n<VertXMessage>\n\n</VertXMessage>'
    context = { 'ip_address': ip_address, 'username': username, 'password':password,
        'xml_request':xml_request, 'xml_response':xml_response}
    return render(request, 'keymaster/test_door.html', context)


######################################################################
# Keymaster API
######################################################################


@csrf_exempt
def keymaster(request):
    try:
        ip = network.get_addr(request)
        keymaster = Keymaster.objects.by_ip(ip)
        if not keymaster:
            raise Exception("No Keymaster for incoming IP (%s)" % ip)
        logger.debug("Incoming connection from: %s" % ip)

        # Decrypt the incoming message
        connection = keymaster.get_encrypted_connection()
        incoming_message = connection.receive_message(request)
        logger.debug("Incoming Message: '%s' " % incoming_message)

        # Process the incoming message
        if incoming_message == Messages.TEST_QUESTION:
            outgoing_message = Messages.TEST_RESPONSE
        elif incoming_message == Messages.GET_TIME:
            return JsonResponse({'text_message':time.strftime("%c")})
        elif incoming_message == Messages.PULL_CONFIGURATION:
            outgoing_message = keymaster.pull_config()
        elif incoming_message == Messages.CHECK_IN:
            outgoing_message = keymaster.check_door_codes()
        elif incoming_message == Messages.PULL_DOOR_CODES:
            outgoing_message = keymaster.pull_door_codes()
        elif incoming_message == Messages.PUSH_EVENT_LOGS:
            incoming_data = connection.data
            #logger.debug("Incoming Data: '%s' " % incoming_data)
            outgoing_message = keymaster.process_event_logs(incoming_data)
        elif incoming_message == Messages.MARK_SUCCESS:
            keymaster.mark_success()
            outgoing_message = Messages.SUCCESS_RESPONSE
        elif incoming_message == Messages.MARK_SYNC:
            keymaster.mark_sync()
            outgoing_message = Messages.SUCCESS_RESPONSE
        elif incoming_message == Messages.LOG_MESSAGE:
            incoming_data = connection.data
            message = incoming_data['log_text']
            keymaster.log_message(message)
            outgoing_message = Messages.SUCCESS_RESPONSE
        else:
            raise Exception("Invalid Message")
        logger.debug("Outgoing Message: '%s' " % outgoing_message)

        # Encrypt our response
        encrypted_response = connection.encrypt_message(outgoing_message)
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return JsonResponse({'error': str(e)})

    return JsonResponse({'message':encrypted_response.decode("utf-8")})


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
