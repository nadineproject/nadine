import time
from datetime import datetime, timedelta, date

from models import *

def handle_uploaded_file(file):
	print(file.name)
	# Expects filename like: arp-111101-0006.txt
	runtime = datetime.strptime(file.name.lstrip("arp-").rstrip(".txt"), "%y%m%d-%H%M")

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