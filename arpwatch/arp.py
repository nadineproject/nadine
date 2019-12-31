import os
import time
import logging
from datetime import datetime, time, date, timedelta

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pytz.exceptions import AmbiguousTimeError

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from arpwatch.models import *

logger = logging.getLogger(__name__)


class ArpImportError(Exception):
    pass

def register_user_ip(user, ip):
    logtime = timezone.localtime(timezone.now())
    logger.info("register_user_ip: Address for %s = %s @ %s" % (user, ip, logtime))
    UserRemoteAddr.objects.create(logintime=logtime, user=user, ip_address=ip)


def device_by_ip(ip):
    end_ts = timezone.localtime(timezone.now())
    start_ts = end_ts - timedelta(minutes=30)
    logs = ArpLog.objects.filter(ip_address=ip, runtime__gte=start_ts, runtime__lte=end_ts).order_by('runtime').reverse()
    if logs.count() > 0:
        latest_log = logs[0]
        if latest_log:
            return latest_log.device


def devices_by_user(user):
    return UserDevice.objects.filter(user=user)


def map_ip_to_mac(hours):
    end_ts = timezone.localtime(timezone.now())
    start_ts = end_ts - timedelta(hours=hours)
    logger.debug("map_ip_to_mac: start=%s, end=%s" % (start_ts, end_ts))
    ip_logs = UserRemoteAddr.objects.filter(logintime__gte=start_ts, logintime__lte=end_ts)
    for i in ip_logs:
        #print("ip_log: %s" % (i))
        arp_logs = ArpLog.objects.filter(ip_address=i.ip_address, runtime__gte=i.logintime - timedelta(minutes=6), runtime__lte=i.logintime + timedelta(minutes=6))[:1]
        for a in arp_logs:
            #print("arp_log: %s" % (a))
            if not a.device.ignore and not a.device.user:
                logger.info("map_ip_to_mac: Associating %s with %s" % (a.device.mac_address, i.user))
                a.device.user = i.user
                a.device.save()


def get_arp_root():
    if not default_storage.exists(settings.ARP_ROOT):
        os.mkdir(default_storage.path(settings.ARP_ROOT))
    return settings.ARP_ROOT


def list_files():
    arp_root = get_arp_root()
    print("listing:")
    print(arp_root)
    file_list = default_storage.listdir(arp_root)[1]
    return file_list


def import_dir_locked():
    arp_root = get_arp_root()
    return default_storage.exists(settings.ARP_IMPORT_LOCK)


def lock_import_dir():
    arp_root = get_arp_root()
    msg = "locked: %s" % timezone.localtime(timezone.now())
    default_storage.save(settings.ARP_IMPORT_LOCK, ContentFile(msg))


def unlock_import_dir():
    default_storage.delete(settings.ARP_IMPORT_LOCK)


def log_message(msg):
    arp_root = get_arp_root()
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
        log = ImportLog.objects.create(file_name=file_name, success=False)

        # Expects filename like: arp-111101-0006.txt
        if file_name.find("arp-") < 0:
            continue
        full_path = settings.ARP_ROOT + file_name

        try:
            # Extract our runtime from the file name
            runtime_str = file_name.lstrip(settings.ARP_ROOT)
            runtime_str = runtime_str.lstrip("arp-").rstrip(".txt")
            runtime = timezone.make_aware(datetime.strptime(runtime_str, "%y%m%d-%H%M"), timezone.get_current_timezone())

            # Import the data
            log_message("importing %s" % file_name)
            file_data = default_storage.open(full_path)
            import_file(file_data, runtime)
            log.success = True
        except AmbiguousTimeError:
            log_message("Caught AmbiguousTimeError.  This must be daylight savings.  Deleting file")
        finally:
            default_storage.delete(full_path)
            log.save()

    # Unlock the import directory
    unlock_import_dir()


def import_file(file):
    import_file(file, file.name)


def import_file(file, runtime):
    with transaction.atomic():
        for chunk in file.chunks():
            for line in chunk.splitlines():
                # Expect line like:
                # ? (172.16.5.153) at 00:1b:21:4e:e7:2c on sk4 expires in 1169 seconds [ethernet]
                line_str = line.decode("utf-8")
                ip = line_str.split("(")[1].split(") at ")[0]
                mac = line_str.split(") at ")[1].split(" on ")[0]

                # Stop me if you think that you've heard this one before
                if ArpLog.objects.filter(runtime=runtime, ip_address=ip).count() > 0:
                    log_message("Data For This Time Already Loaded: %s" % runtime)
                    return

                log_data(runtime, ip, mac)


def import_snmp():
    if not hasattr(settings, "ARPWATCH_SNMP_SERVER"):
        raise ArpImportError("Missing ARPWATCH_SNMP_SERVER setting")
    if not hasattr(settings, "ARPWATCH_SNMP_COMMUNITY"):
        raise ArpImportError("Missing ARPWATCH_SNMP_COMMUNITY setting")
    if not hasattr(settings, "ARPWATCH_NETWORK_PREFIX"):
        raise ArpImportError("Missing ARPWATCH_NETWORK_PREFIX setting")

    # Mark the time
    runtime = timezone.now()

    # Fire off the SNMP command
    logger.debug("connecting to %s..." % settings.ARPWATCH_SNMP_SERVER)
    cmdGen = cmdgen.CommandGenerator()
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(
        cmdgen.CommunityData(settings.ARPWATCH_SNMP_COMMUNITY),
        cmdgen.UdpTransportTarget((settings.ARPWATCH_SNMP_SERVER, 161)),
        cmdgen.MibVariable('IP-MIB', 'ipNetToMediaPhysAddress'),
        lookupNames=True, lookupValues=True
    )
    if errorIndication:
        raise errorIndication

    # Extract the MAC Addresses and IP Addresses from the data
    for row in varBinds:
        print(row)
        for name, val in row:
            long_name = name.prettyPrint()
            # Search data returned for an IP address
            if settings.ARPWATCH_NETWORK_PREFIX in long_name:
                ip_index = long_name.index(settings.ARPWATCH_NETWORK_PREFIX)
                ip = long_name[ip_start:]
                mac = val.prettyPrint()
                # print(f"{mac} = {ip}")
                log_data(runtime, ip, mac)


def log_data(runtime, ip, mac):
    # User Device
    if UserDevice.objects.filter(mac_address=mac).count() > 0:
        device = UserDevice.objects.get(mac_address=mac)
    else:
        device = UserDevice.objects.create(mac_address=mac)

    # ArpLog
    return ArpLog.objects.create(runtime=runtime, ip_address=ip, device=device)


def day_is_complete(day_str):
    # Return true if there are evenly spaced logs throughout the day
    day_start = datetime.strptime(day_str + " 00:00", "%Y-%m-%d %H:%M")
    day_end = datetime.strptime(day_str + " 23:59", "%Y-%m-%d %H:%M")
    arp_logs = ArpLog.objects.filter(runtime__gt=day_start, runtime__lt=day_end).order_by('runtime')
    print((arp_logs.count()))
    return True


def device_users_for_day(day=None):
    if not day:
        day = timezone.localtime(timezone.now())
    start = datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)
    start = timezone.make_aware(start, timezone.get_current_timezone())
    end = start + timedelta(days=1)
    query = ArpLog.objects.filter(runtime__range=(start, end)).order_by('device__user').distinct('device__user')
    return query.values('device__user', 'runtime')


def users_for_day_query(day=None):
    if not day:
        day = timezone.localtime(timezone.now())
    start = datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)
    start = timezone.make_aware(start, timezone.get_current_timezone())
    end = start + timedelta(days=1)
    logger.info("users_for_day from '%s' to '%s'" % (start, end))
    arp_query = ArpLog.objects.filter(runtime__range=(start, end), device__ignore=False)
    return User.objects.filter(id__in=arp_query.values('device__user'))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
