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
        self.room1 = Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00)
        self.room2 = Room.objects.create(name="Room 2", has_phone=True, has_av=True, floor=1, seats=2, max_capacity=4, default_rate=20.00)

    def test_available_floor(self):
        rooms = Room.objects.available(floor=1)
        self.assertTrue(len(rooms) > 0)
        rooms = Room.objects.available(floor=2)
        self.assertTrue(len(rooms) == 0)

    def test_available_seats(self):
        rooms = Room.objects.available(seats=1)
        self.assertTrue(len(rooms) > 0)
        rooms = Room.objects.available(seats=5)
        self.assertTrue(len(rooms) == 0)

    def test_available_av(self):
        rooms = Room.objects.available(has_av=True)
        self.assertEquals(len(rooms), 1)
        self.assertTrue(rooms[0].has_av)
        rooms = Room.objects.available(has_av=False)
        self.assertEquals(len(rooms), 1)
        self.assertFalse(rooms[0].has_av)

    def test_available_phone(self):
        rooms = Room.objects.available(has_phone=True)
        self.assertEquals(len(rooms), 1)
        self.assertTrue(rooms[0].has_phone)
        rooms = Room.objects.available(has_phone=False)
        self.assertEquals(len(rooms), 1)
        self.assertFalse(rooms[0].has_phone)
