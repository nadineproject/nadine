import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from nadine.models import *

class RoomTestCase(TestCase):

    def setUp(self):
        self.room1 = Room.objects.create(name="Room 1", floor=1, seats=4, max_capacity=10, default_rate=20.00)

    def test_available(self):
        start = None
        end = None
        rooms = Room.objects.available(start, end)
        self.assertTrue(len(rooms) > 0)
