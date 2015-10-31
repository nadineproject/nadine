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

def get_gatekeeper_message(request):
    # Verify the IP address of the gatekeeper
    ip = get_client_ip(request)
    if not ip == settings.HID_GATEKEEPER_IP:
        raise Exception("invalid IP (%s)" % ip)
    print "Incoming message from: %s" % ip
    
    # Grab our encryption key
    encryption_key = settings.HID_ENCRYPTION_KEY
    if not encryption_key:
        raise Exception("No encryption key")

    # Encrypted message is in 'message' POST variable
    if not 'message' in request.POST:
        raise Exception("No message in POST")

    # Decrypt the message
    encrypted_message = request.POST['message']
    f = Fernet(encryption_key)
    decrypted_message = f.decrypt(bytes(encrypted_message))

    return decrypted_message

@csrf_exempt
def keymaster(request):
    try:
        incoming_message = get_gatekeeper_message(request)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    print "Message: %s" % incoming_message

    #new_codes = DoorCode.objects.all()
    #response = {'new_codes': new_codes}
    
    return JsonResponse({'success':True})
