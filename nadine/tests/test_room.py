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
        self.user1 = User.objects.create(username='user_one', first_name='User', last_name='One')

        self.room1 = Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00)
        self.room2 = Room.objects.create(name="Room 2", has_phone=True, has_av=True, floor=1, seats=2, max_capacity=4, default_rate=20.00)

        start = timezone.now()
        end = timezone.now() + timedelta(hours=3)
        self.event1 = Event.objects.create(user=self.user1, room=self.room1, start_ts=start, end_ts=end)

    def test_available_start(self):
        start = timezone.now()
        end = timezone.now() + timedelta(hours=2)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(rooms[0] == self.room2)
        self.assertFalse(rooms[0] == self.room1)

    def test_available_straddling(self):
        start = timezone.now()
        end = timezone.now() + timedelta(hours=1)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(len(rooms) == 1)
        self.assertTrue(rooms[0] == self.room2)

    def test_available_sandwich(self):
        start = timezone.now() - timedelta(hours=1)
        end =  timezone.now() + timedelta(minutes=30)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 1)
        self.assertTrue(rooms[0] == self.room2)

    def test_available_overlap(self):
        start = timezone.now() + timedelta(hours=1)
        end = timezone.now() + timedelta(hours=2)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 1)
        self.assertFalse(rooms[0] == self.room1)

    def test_available_early(self):
        start = timezone.now() - timedelta(hours=2)
        end = timezone.now() - timedelta(hours=1)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 2)
        self.assertTrue(rooms[0] == self.room1)

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
        self.assertEquals(self.room2, rooms[0])
        self.assertTrue(rooms[0].has_av)
        rooms = Room.objects.available(has_av=False)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_av)

    def test_available_phone(self):
        rooms = Room.objects.available(has_phone=True)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room2, rooms[0])
        self.assertTrue(rooms[0].has_phone)
        rooms = Room.objects.available(has_phone=False)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_phone)

    def test_get_raw_calendar(self):
        settings.OPEN_TIME = "8:00"
        settings.CLOSE_TIME = "18:00"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEquals(len(calendar1), 40)
        self.assertEquals(calendar1[0]['hour'], '8')
        self.assertEquals(calendar1[0]['minutes'], '00')
        self.assertEquals(calendar1[1]['hour'], '8')
        self.assertEquals(calendar1[1]['minutes'], '15')
        self.assertEquals(calendar1[2]['hour'], '8')
        self.assertEquals(calendar1[2]['minutes'], '30')
        self.assertEquals(calendar1[3]['hour'], '8')
        self.assertEquals(calendar1[3]['minutes'], '45')
        self.assertEquals(calendar1[4]['hour'], '9')
        self.assertEquals(calendar1[4]['minutes'], '00')
        self.assertEquals(calendar1[39]['hour'], '5')
        self.assertEquals(calendar1[39]['minutes'], '45')

    def test_get_raw_calendar2(self):
        settings.OPEN_TIME = "7:30"
        settings.CLOSE_TIME = "18:30"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEquals(len(calendar1), 44)
        self.assertEquals(calendar1[0]['hour'], '7')
        self.assertEquals(calendar1[0]['minutes'], '30')
        self.assertEquals(calendar1[43]['hour'], '6')
        self.assertEquals(calendar1[43]['minutes'], '15')
