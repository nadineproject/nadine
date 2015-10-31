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

from cryptography.fernet import Fernet

from hid.models import *

@staff_member_required
def index(request):
    return render_to_response('hid/index.html', {}, context_instance=RequestContext(request))

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
        #print "Incoming message from: %s" % ip

        # Encrypted message is in 'message' POST variable
        if not 'message' in request.POST:
            raise Exception("No message in POST")
        encrypted_message = request.POST['message']

        # Decrypt the message
        incoming_message = request.POST['message']
        response_message = gatekeeper.process_message(incoming_message)
    except Exception as e:
        return JsonResponse({'error': str(e)})

    return JsonResponse({'message':response_message})
