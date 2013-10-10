import time
from datetime import datetime, time, date, timedelta

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from models import *
from staff.models import Member, DailyLog

def register_user_ip(user, ip):
	print("REMOTE_ADDR for %s: %s" % (user, ip))
	ip_log = UserRemoteAddr.objects.create(logintime=timezone.localtime(timezone.now()), user=user, ip_address=ip)

def map_ip_to_mac(hours):
	end_ts = timezone.localtime(timezone.now())
	start_ts = end_ts - timedelta(hours=hours)
	ip_logs = UserRemoteAddr.objects.filter(logintime__gte=start_ts, logintime__lte=end_ts)
	for i in ip_logs:
		#print("ip_log: %s" % (i))
		arp_logs = ArpLog.objects.filter(ip_address=i.ip_address, runtime__gte=i.logintime-timedelta(minutes=6), runtime__lte=i.logintime+timedelta(minutes=6))[:1]
		for a in arp_logs:
			#print("arp_log: %s" % (a))
			if not a.device.ignore and not a.device.user:
				#print("FOUND ONE! %s = %s" % (a.device.mac_address, i.user))
				a.device.user = i.user
				a.device.save()

def list_files():
	print("listing:" )
	print(settings.ARP_ROOT)
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	return file_list

def import_dir_locked():
	return default_storage.exists(settings.ARP_IMPORT_LOCK)

def lock_import_dir():
	msg = "locked: %s" % timezone.localtime(timezone.now())
	default_storage.save(settings.ARP_IMPORT_LOCK, ContentFile(msg))

def unlock_import_dir():
	default_storage.delete(settings.ARP_IMPORT_LOCK)

def log_message(msg):
	log = "%s: %s\r\n" % (timezone.localtime(timezone.now()), msg)
	if not default_storage.exists(settings.ARP_IMPORT_LOG):
		log = "%s: Log Started\r\n%s" % (timezone.localtime(timezone.now()), log)
	log_file = default_storage.open(settings.ARP_IMPORT_LOG, mode="a")
	log_file.write(log)
	log_file.close()
	
def import_all():
	if import_dir_locked():
		return

	# Lock the import directory
	lock_import_dir()
	
	file_list = default_storage.listdir(settings.ARP_ROOT)[1]
	for file_name in file_list:
		# Expects filename like: arp-111101-0006.txt
		if file_name.find("arp-") < 0:
			continue
		runtime_str = file_name.lstrip(settings.ARP_ROOT)
		runtime_str = runtime_str.lstrip("arp-").rstrip(".txt")
		runtime = timezone.make_aware(datetime.strptime(runtime_str, "%y%m%d-%H%M"), timezone.get_current_timezone())
		full_path = settings.ARP_ROOT + file_name
		file = default_storage.open(full_path)	
		log_message("importing %s" % file_name)
		ImportLog.objects.create(file_name=file_name, success=False)
		import_file(file, runtime)
		default_storage.delete(full_path)
		log = ImportLog.objects.filter(file_name=file_name).order_by('created')[0]
		log.success = True
		log.save()
		
	# Unlock the import directory
	unlock_import_dir()

def import_file(file):
	import_file(file, file.name)

def import_file(file, runtime):
	with transaction.commit_on_success():
		for chunk in file.chunks():
			for line in chunk.splitlines():
				# Expect line like:
				# ? (172.16.5.153) at 00:1b:21:4e:e7:2c on sk4 expires in 1169 seconds [ethernet]
				ip = line.split("(")[1].split(") at ")[0]
				mac = line.split(") at ")[1].split(" on ")[0]

				# Stop me if you think that you've heard this one before
				if ArpLog.objects.filter(runtime=runtime, ip_address=ip).count() > 0:
					log_message("Data For This Time Already Loaded: %s" % runtime)
					return

				# User Device
				if UserDevice.objects.filter(mac_address=mac).count() > 0:
					device = UserDevice.objects.get(mac_address=mac)
				else:
					device = UserDevice.objects.create(mac_address=mac)

				# ArpLog
				ArpLog.objects.create(runtime=runtime, ip_address=ip, device=device)

def day_is_complete(day_str):
	# Return true if there are evenly spaced logs throughout the day
	day_start = datetime.strptime(day_str + " 00:00", "%Y-%m-%d %H:%M")
	day_end = datetime.strptime(day_str + " 23:59", "%Y-%m-%d %H:%M")
	arp_logs = ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime')
	print(arp_logs.count())
	return True
	
def device_users_for_day(day=date.today()):
	start = datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)
	start = timezone.make_aware(start, timezone.get_current_timezone())
	end = start + timedelta(days=1)
	query = ArpLog.objects.filter(runtime__range=(start, end)).order_by('device__user').distinct('device__user')
	return query.values('device__user', 'runtime')

def users_for_day(day=date.today()):
	member_dict = {}

	# Who's signed into the space today
	daily_logs = DailyLog.objects.filter(visit_date=day)
	for l in daily_logs:
		member_dict[l.member] = l.created

	# Device Logs
	for l in device_users_for_day(day):
		member = l.get_profile()
		if not member_dict.has_key(member) or l.runtime < member_dict[member]:
			member_dict[member] = l.runtime
	
	members = sorted(member_dict, key=member_dict.get)
	members.reverse()
	return members
