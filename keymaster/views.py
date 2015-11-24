from datetime import datetime, timedelta, date

from django.conf import settings
from django.template import RequestContext
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.http import Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from keymaster.hid_control import DoorController
from keymaster.models import *


@staff_member_required
def index(request):
    return render_to_response('keymaster/index.html', {}, context_instance=RequestContext(request))


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
        gatekeeper = Gatekeeper.objects.by_ip(ip)
        if not gatekeeper:
            raise Exception("No Gatekeeper for incoming IP (%s)" % ip)
        logger.debug("Incoming connection from: %s" % ip)

        keymaster = Keymaster(gatekeeper)
        connection = keymaster.encrypted_connection
        incoming_message = connection.receive_message(request)
        outgoing_message = keymaster.process_message(incoming_message)
        encrypted_response = connection.encrypt_message(outgoing_message)
    except Exception as e:
        return JsonResponse({'error': str(e)})

    return JsonResponse({'message':encrypted_response})
