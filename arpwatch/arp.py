import time
from datetime import datetime, timedelta, date

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from models import *

def register_user_ip(user, ip):
	print("REMOTE_ADDR for %s: %s" % (user, ip))
	ip_log = UserRemoteAddr.objects.create(logintime=datetime.now(), user=user, ip_address=ip)
	
#	if ip:
#		if ip.find(settings.ARP_IP_PFX) != 0:
#			return
#	if UserDevice.objects.filter(user=user).count() == 0:
#		nowish = datetime.now() - timedelta(minutes=12)
#		for log in ArpLog.objects.filter(runtime__gt=nowish, ip_address=ip).order_by('runtime'):
#			if not log.device.user:
#				log.device.user = user
#				log.save()
#			return

def list_files():
	print("listing:" )
	print(settings.ARP_ROOT)
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	return file_list

def import_dir_locked():
	return default_storage.exists(settings.ARP_IMPORT_LOCK)

def lock_import_dir():
	msg = "locked: %s" % datetime.now()
	default_storage.save(settings.ARP_IMPORT_LOCK, ContentFile(msg))

def unlock_import_dir():
	default_storage.delete(settings.ARP_IMPORT_LOCK)

def log_message(msg):
	log = "%s: %s\r\n" % (datetime.now(), msg)
	if not default_storage.exists(settings.ARP_IMPORT_LOG):
		log = "%s: Log Started\r\n%s" % (datetime.now(), log)
	log_file = default_storage.open(settings.ARP_IMPORT_LOG, mode="wb")
	log_file.write(log)
	log_file.close()
	
def import_all():
	if import_dir_locked():
		raise RuntimeError('Import Directory Locked')

	# Lock the import directory
	lock_import_dir()
	
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	for file_name in file_list:
		# Expects filename like: arp-111101-0006.txt
		if file_name.find("arp-") < 0:
			continue
		runtime_str = file_name.lstrip(settings.ARP_ROOT)
		runtime_str = runtime_str.lstrip("arp-").rstrip(".txt")
		runtime = datetime.strptime(runtime_str, "%y%m%d-%H%M")
		full_path = settings.ARP_ROOT + file_name
		file = default_storage.open(full_path)
		log_message("importing %s" % file_name)
		import_file(file, runtime)
		default_storage.delete(full_path)
		
	# Unlock the import directory
	unlock_import_dir()

def import_file(file):
	import_file(file, file.name)

def import_file(file, runtime):
	for chunk in file.chunks():
		for line in chunk.splitlines():
			# Expect line like:
			# ? (172.16.5.153) at 00:1b:21:4e:e7:2c on sk4 expires in 1169 seconds [ethernet]
			ip = line.split("(")[1].split(") at ")[0]
			mac = line.split(") at ")[1].split(" on ")[0]

			# Stop me if you think that you've heard this one before
			if ArpLog.objects.filter(runtime=runtime, ip_address=ip).count() > 0:
				raise RuntimeError('Data Already Loaded')

			# User Device
			if UserDevice.objects.filter(mac_address=mac).count() > 0:
				device = UserDevice.objects.get(mac_address=mac)
			else:
				device = UserDevice.objects.create(mac_address=mac)

			# Create a log entry
			log = ArpLog.objects.create(runtime=runtime, ip_address=ip, device=device)

def day_is_complete(day_str):
	# Return true if there are evenly spaced logs throughout the day
	day_start = datetime.strptime(day_str + " 00:00", "%Y-%m-%d %H:%M")
	day_end = datetime.strptime(day_str + " 23:59", "%Y-%m-%d %H:%M")
	arp_logs = ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime')
	print(arp_logs.count())
	return True
