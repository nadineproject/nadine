import json
import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.db import IntegrityError

import arp
from arpwatch.models import *

class ArpWatchTest(TestCase):

	def test_api(self):
		response = self.client.get('/api/v1/activity/0/')
		self.failUnlessEqual(response.status_code, 200, 'status was %s' % response.status_code)
		result_data = json.loads(response.content)
		self.failUnless('member_count' in result_data)
		
	def test_user_device(self):
		MAC = "90:A2:DA:00:EE:5D"
		device1 = UserDevice.objects.create(mac_address=MAC)
		with self.assertRaises(IntegrityError):
			device2 = UserDevice.objects.create(mac_address=MAC)
		
	def test_dir_lock(self):
		self.assertFalse(arp.import_dir_locked())
		arp.lock_import_dir()
		self.assertTrue(arp.import_dir_locked())
		arp.unlock_import_dir()
		self.assertFalse(arp.import_dir_locked())

	def test_log_message(self):
		arp.log_message("testing")
		#self.assertFalse(arp.import_dir_locked())
		
	#def test_arpwatch(self):
		#mac1 = MACAddress.objects.create(value="90:A2:DA:00:EE:5D")
		#ip1 = IPAddress.objects.create(value="127.0.0.1")
		#mac2 = MACAddress.objects.create(value='AA:AA:AA:AA:AA:AA')
		#ip2 = IPAddress.objects.create(value='192.168.1.1')
		#mac3 = MACAddress.objects.create(value='BB:BB:BB:BB:BB:BB')
		#ip3 = IPAddress.objects.create(value='172.16.5.1')

		#arp_entries = []
		#arp_entries.append(ArpLogEntry.objects.create(mac=mac1, ip=ip1))
		#arp_entries.append(ArpLogEntry.objects.create(mac=mac2, ip=ip2))
		#arp_entries.append(ArpLogEntry.objects.create(mac=mac3, ip=ip3))

		#arp_log = ArpLog.objects.create()
		#arp_log.entries = arp_entries;
		
		#self.assertEqual("90:A2:DA:00:EE:5D", mac1.value)
		#self.assertEqual("127.0.0.1", ip1.value)
