from datetime import datetime, timedelta, date

from django.db.models import Q
from django.contrib import auth
from django.conf import settings
from django.template import RequestContext
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect

from forms import *
from models import *

import arp
from staff.models import Member

def index(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			file = request.FILES['file']
			if (UploadLog.objects.filter(file_name=file.name).count() > 0):
				raise Exception('File Already Loaded')
			if request.user.is_authenticated():
				UploadLog.objects.create(user=request.user, file_name=file.name, file_size=file.size)
			else:
				UploadLog.objects.create(file_name=file.name, file_size=file.size)
			arp.handle_uploaded_file(file)
			#return HttpResponseRedirect('/success/url/')
	else:
		 form = UploadFileForm()
	
	return render_to_response('arpwatch/index.html', {'form': form}, context_instance=RequestContext(request))

def device_list(request):
	return render_to_response('arpwatch/devices.html', {'devices': UserDevice.objects.all()}, context_instance=RequestContext(request))

def device(request, id):
	device = UserDevice.objects.get(pk=id)
	logs = ArpLog.objects.filter(device=device).order_by('runtime')
	return render_to_response('arpwatch/device.html', {'device': device, 'arp_logs': logs}, context_instance=RequestContext(request))


# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
