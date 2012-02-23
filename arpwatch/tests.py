import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings

from arpwatch.models import MACAddress, IPAddress, ArpLog, ArpLogEntry

class PFWatchTest(TestCase):

	def test_arpwatch(self):
		mac1 = MACAddress.objects.create(value="90:A2:DA:00:EE:5D")
		ip1 = IPAddress.objects.create(value="127.0.0.1")
		mac2 = MACAddress.objects.create(value='AAAAAAAAAAAA')
		ip2 = IPAddress.objects.create(value='192.168.1.1')
		mac3 = MACAddress.objects.create(value='BBBBBBBBBBBB')
		ip3 = IPAddress.objects.create(value='172.16.5.1')
		arp_log = ArpLog.objects.create()
		log_entry = ArpLogEntry.objects.create(log=arp_log, mac=mac1, ip=ip1)
		log_entry = ArpLogEntry.objects.create(log=arp_log, mac=mac2, ip=ip2)
		log_entry = ArpLogEntry.objects.create(log=arp_log, mac=mac3, ip=ip3)
		
		self.assertEqual("90:A2:DA:00:EE:5D", mac1.value)
		self.assertEqual("127.0.0.1", ip1.value)
