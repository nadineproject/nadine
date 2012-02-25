import time
from datetime import datetime, timedelta, date
from django.conf import settings
from django.core.files.storage import default_storage

from models import *

def list_files():
	print("listing:" )
	print(settings.ARP_ROOT)
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	return file_list

def import_all():
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	for file_name in file_list:
		full_path = settings.ARP_ROOT + file_name
		print(full_path)
		file = default_storage.open(full_path)
		import_file(file, file_name)

def import_file(file):
	import_file(file, file.name)

def import_file(file, file_name):
	# Expects filename like: arp-111101-0006.txt
	runtime_str = file_name.lstrip(settings.ARP_ROOT)
	runtime_str = runtime_str.lstrip("arp-").rstrip(".txt")
	print(runtime_str)
	runtime = datetime.strptime(runtime_str, "%y%m%d-%H%M")

	for chunk in file.chunks():
		for line in chunk.splitlines():
			# Expect line like:
			# ? (172.16.5.153) at 00:1b:21:4e:e7:2c on sk4 expires in 1169 seconds [ethernet]
			ip = line.split("(")[1].split(") at ")[0]
			mac = line.split(") at ")[1].split(" on ")[0]

			# Stop me if you think that you've heard this one before
			if ArpLog.objects.filter(runtime=runtime, ip_address=ip).count() > 0:
				raise Exception('Data Already Loaded')
				
			# User Device
			if UserDevice.objects.filter(mac_address=mac).count() > 0:
				device = UserDevice.objects.get(mac_address=mac)
			else:
				device = UserDevice.objects.create(mac_address=mac)

			# Create a log entry
			log = ArpLog.objects.create(runtime=runtime, ip_address=ip, device=device)
			print(log)

def day_is_complete(day_str):
	# Return true if there are evenly spaced logs throughout the day
	day_start = datetime.strptime(day_str + " 00:00", "%Y-%m-%d %H:%M")
	day_end = datetime.strptime(day_str + " 23:59", "%Y-%m-%d %H:%M")
	arp_logs = ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime')
	print(arp_logs.count())
	return True
