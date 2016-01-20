import logging
from datetime import datetime, timedelta, date

from django.conf import settings
from django.template import RequestContext
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from doors.hid_control import DoorController
from doors.keymaster.models import Keymaster, Door, DoorCode, DoorEvent
from doors.core import EncryptedConnection, Messages, DoorEventTypes

logger = logging.getLogger(__name__)


@staff_member_required
def index(request):
    keymasters = Keymaster.objects.filter(is_enabled=True)
    twoMinutesAgo = timezone.now() - timedelta(minutes=2)
    events = DoorEvent.objects.all().order_by('timestamp').reverse()[:10]
    return render_to_response('keymaster/index.html', 
        {'keymasters': keymasters, 
         'twoMinutesAgo': twoMinutesAgo,
         'events': events,
        }, 
        context_instance=RequestContext(request))


@staff_member_required
def user_keys(request, username):
    user = get_object_or_404(User, username=username)
    keys = DoorCode.objects.filter(user=user)
    logs = DoorEvent.objects.filter(user=user)
    
    tenMinutesAgo = timezone.now() - timedelta(minutes=10)
    potential_keys = DoorEvent.objects.filter(timestamp__gte=tenMinutesAgo, event_type=DoorEventTypes.UNRECOGNIZED)
    
    if 'code_id' in request.POST and request.POST.get('action') == "Delete":
        door_code = get_object_or_404(DoorCode, id=request.POST.get('code_id'))
        door_code.delete()
    
    if not 'view_all_logs' in request.GET:
        logs = logs[:10]
    return render_to_response('keymaster/user_keys.html', {'user':user, 'keys':keys, 'logs':logs, 'potential_keys':potential_keys}, context_instance=RequestContext(request))


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
        print door_code
    
    # Save the code if we've received user confirmation
    if door_code and 'add_door_code' in request.POST:
        door_code.save()
        return HttpResponseRedirect(reverse('doors.views.user_keys', kwargs={'username': user.username}))
    
    return render_to_response('keymaster/add_key.html', {'username':username, 'code':code, 'door_code':door_code}, context_instance=RequestContext(request))


@staff_member_required
def test_door(request):
    ip_address = request.POST.get("ip_address", "")
    username = request.POST.get("username", "")
    password = request.POST.get("password", "")
    xml_request = request.POST.get("xml_request", "")
    xml_response = ""
    if len(xml_request) > 0:
        start_ts = timezone.now()
        controller = DoorController(ip_address, username, password)
        response_code, xml_response = controller.send_xml_str(xml_request)
        response_time = timezone.now() - start_ts
        print "response code: %d, response time: %s" % (response_code, response_time)
    else:
        # Start with the basic framework    
        xml_request = '<?xml version="1.0" encoding="UTF-8"?>\n<VertXMessage>\n\n</VertXMessage>'
    return render_to_response('keymaster/test_door.html', { 'ip_address': ip_address,
        'username': username, 'password':password, 'xml_request':xml_request, 'xml_response':xml_response
    }, context_instance=RequestContext(request))


######################################################################
# Keymaster API 
######################################################################


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def keymaster(request):
    try:
        ip = get_client_ip(request)
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
        else:
            raise Exception("Invalid Message")
        logger.debug("Outgoing Message: '%s' " % outgoing_message)
        
        # Encrypt our response
        encrypted_response = connection.encrypt_message(outgoing_message)
    except Exception as e:
        logger.error(e)
        return JsonResponse({'error': str(e)})

    return JsonResponse({'message':encrypted_response})
