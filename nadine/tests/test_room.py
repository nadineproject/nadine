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

        # With these 2 events, Room1 is booked for the next 5 hours and Room2 is available.

        # Event in Room1 starting now for the next 3 hours.
        self.start1 = timezone.now()
        self.end1 = self.start1 + timedelta(hours=3)
        self.event1 = Event.objects.create(user=self.user1, room=self.room1, start_ts=self.start1, end_ts=self.end1)

        # Event in Room1 starting after Event1 and lasting 2 hours.
        self.start2 = self.end1
        self.end2 = self.start2 + timedelta(hours=2)
        self.event2 = Event.objects.create(user=self.user1, room=self.room1, start_ts=self.start2, end_ts=self.end2)

    def test_available(self):
        # Only Room2 is available now.
        rooms = Room.objects.available()
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(rooms[0] == self.room2)
        self.assertFalse(rooms[0] == self.room1)

    def test_available_straddling(self):
        # Check for a room in 1 hour for 1 hour.
        # This event straddles Event1.
        start = timezone.now() + timedelta(hours=1)
        end = timezone.now() + timedelta(hours=1)
        # We should get only Room2.
        rooms = Room.objects.available(start=start, end=end)
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
        self.assertTrue(self.room2 in rooms)
        self.assertFalse(self.room1 in rooms)

    def test_available_early(self):
        start = timezone.now() - timedelta(hours=2)
        end = timezone.now() - timedelta(hours=1)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 2)
        self.assertTrue(self.room1 in rooms)
        self.assertTrue(self.room2 in rooms)

    def test_available_floor(self):
        rooms = Room.objects.available(floor=1)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(self.room2 in rooms)
        rooms = Room.objects.available(floor=2)
        self.assertTrue(len(rooms) == 0)

    def test_available_seats(self):
        rooms = Room.objects.available(seats=1)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(self.room2 in rooms)
        rooms = Room.objects.available(seats=5)
        self.assertTrue(len(rooms) == 0)

    def test_available_av(self):
        # Look for rooms with AV starting tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        rooms = Room.objects.available(start=tomorrow, has_av=True)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room2, rooms[0])
        self.assertTrue(rooms[0].has_av)
        rooms = Room.objects.available(start=tomorrow, has_av=False)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_av)

    def test_available_phone(self):
        # Look for rooms with a phoen starting tomorrow
        tomorrow = timezone.now() + timedelta(days=1)
        rooms = Room.objects.available(start=tomorrow, has_phone=True)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room2, rooms[0])
        self.assertTrue(rooms[0].has_phone)
        rooms = Room.objects.available(start=tomorrow, has_phone=False)
        self.assertEquals(len(rooms), 1)
        self.assertEquals(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_phone)

    def test_get_raw_calendar(self):
        settings.OPEN_TIME = "8:00"
        settings.CLOSE_TIME = "18:00"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEquals(len(calendar1), 40)
        self.assertEquals(calendar1[0]['hour'], '8')
        self.assertEquals(calendar1[0]['mil_hour'], '8')
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
        self.assertEquals(calendar1[39]['mil_hour'], '17')
        self.assertEquals(calendar1[39]['minutes'], '45')

    def test_get_raw_calendar2(self):
        settings.OPEN_TIME = "7:30"
        settings.CLOSE_TIME = "18:30"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEquals(len(calendar1), 44)
        self.assertEquals(calendar1[0]['hour'], '7')
        self.assertEquals(calendar1[0]['mil_hour'], '7')
        self.assertEquals(calendar1[0]['minutes'], '30')
        self.assertEquals(calendar1[43]['hour'], '6')
        self.assertEquals(calendar1[43]['mil_hour'], '18')
        self.assertEquals(calendar1[43]['minutes'], '15')

    def test_get_calendar(self):
        calendar = self.room1.get_calendar()
        print calendar
        reserved_count = 0
        for block in calendar:
            if 'reserved' in block and block['reserved']:
                reserved_count = reserved_count + 1
        self.assertEquals(reserved_count, 20)
