import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.timezone import localtime, now
from nadine.models import *

class RoomTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create(username='user_one', first_name='User', last_name='One')

        self.room1 = Room.objects.create(name="Room 1", has_phone=False, has_av=False, floor=1, seats=4, max_capacity=10, default_rate=20.00, members_only=True)
        self.room2 = Room.objects.create(name="Room 2", has_phone=True, has_av=True, floor=1, seats=2, max_capacity=4, default_rate=20.00, members_only=False)

        # With these 2 events, Room1 is booked for the next 5 hours and Room2 is available.

        # Event in Room1 starting today at 11AM for the 3 hours.
        self.start1 = localtime(now()).replace(hour=11, minute=0)
        self.end1 = self.start1 + timedelta(hours=3)
        self.event1 = Event.objects.create(user=self.user1, room=self.room1, start_ts=self.start1, end_ts=self.end1)

        # Event in Room1 starting after Event1 and lasting 2 hours.
        self.start2 = self.end1
        self.end2 = self.start2 + timedelta(hours=2)
        self.event2 = Event.objects.create(user=self.user1, room=self.room1, start_ts=self.start2, end_ts=self.end2)

        # Event in Room1 starting at 3 and going until 4
        # self.start2 = self.start1 + timedelta(hours=5)
        # self.end2 = self.start2 + timedelta(hours=1)
        # self.event3 = Event.objects.create(user=self.user1, room=self.room1, start_ts=self.start2, end_ts=self.end2)

    def test_available(self):
        # Only Room2 is available at 11:00.
        rooms = Room.objects.available(start=localtime(now()).replace(hour=11, minute=0))
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(rooms[0] == self.room2)
        self.assertFalse(rooms[0] == self.room1)

    def test_available_early(self):
        #Check for room for search which starts and ends before any saved events
        start = self.start1 - timedelta(hours=2)
        end = start + timedelta(hours=1)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(len(rooms) == 2)
        self.assertTrue(self.room1 in rooms)
        self.assertTrue(self.room2 in rooms)

    def test_available_flush_start(self):
        #Check for a room for event that ends at start of another event
        start = self.start1 - timedelta(hours=1)
        end = self.start1
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(len(rooms) == 2)
        self.assertTrue(self.room1 in rooms)
        self.assertTrue(self.room2 in rooms)

    def test_available_flush_end(self):
        #Check for a room for event that starts at end of another event
        start = self.end2
        end = start + timedelta(hours=1)
        rooms=Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) > 0)
        self.assertTrue(len(rooms) == 2)
        self.assertTrue(self.room1 in rooms)
        self.assertTrue(self.room2 in rooms)

    # def test_available_middle_opening(self):
        # To run this test, comment out Event2 and uncomment out Event3
        # Check for room available in between two bookings
        # start = self.end1
        # end = start + timedelta(hours=1)
        # rooms = Room.objects.available(start=start, end=end)
        # self.assertTrue(len(rooms) == 2)

    def test_available_middle(self):
        # Check for a room in 1 hour for 1 hour.
        # This event straddles Event1.
        start = self.start1 + timedelta(hours=1)
        end = start + timedelta(hours=1)
        # We should get only Room2.
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 1)
        self.assertTrue(rooms[0] == self.room2)


    def test_available_head(self):
        #Check for room starting before saved event and ends after event start
        start = self.start1 - timedelta(hours=1)
        end =  self.start1 + timedelta(minutes=30)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 1)
        self.assertTrue(rooms[0] == self.room2)

    def test_available_tail(self):
        #Check for room with event starting before Event1 and ends after Event1 ends
        start = self.start1 - timedelta(hours=1)
        end = self.end1 + timedelta(hours=1)
        rooms = Room.objects.available(start=start, end=end)
        self.assertTrue(len(rooms) == 1)
        self.assertTrue(self.room2 in rooms)
        self.assertFalse(self.room1 in rooms)

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
        tomorrow = localtime(now()) + timedelta(days=1)
        rooms = Room.objects.available(start=tomorrow, has_av=True)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(self.room2, rooms[0])
        self.assertTrue(rooms[0].has_av)
        rooms = Room.objects.available(start=tomorrow, has_av=False)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_av)

    def test_available_phone(self):
        # Look for rooms with a phoen starting tomorrow
        tomorrow = localtime(now()) + timedelta(days=1)
        init_rooms = Room.objects.available(start=tomorrow, has_phone=True)
        self.assertEqual(len(init_rooms), 1)
        self.assertEqual(self.room2, init_rooms[0])
        self.assertTrue(init_rooms[0].has_phone)
        rooms = Room.objects.available(start=tomorrow, has_phone=False)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(self.room1, rooms[0])
        self.assertFalse(rooms[0].has_phone)

    def test_available_members_only(self):
        tomorrow = localtime(now()) + timedelta(days=1)
        init_rooms = Room.objects.available(start=tomorrow, members_only=True)
        self.assertEqual(len(init_rooms), 1)
        self.assertEqual(self.room1, init_rooms[0])
        self.assertTrue(init_rooms[0].members_only)
        rooms = Room.objects.available(start=tomorrow, members_only=False)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(self.room2, rooms[0])
        self.assertFalse(rooms[0].members_only)

    def test_get_raw_calendar(self):
        settings.OPEN_TIME = "8:00"
        settings.CLOSE_TIME = "18:00"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEqual(len(calendar1), 40)
        self.assertEqual(calendar1[0]['hour'], '8')
        self.assertEqual(calendar1[0]['mil_hour'], '8')
        self.assertEqual(calendar1[0]['minutes'], '00')
        self.assertEqual(calendar1[1]['hour'], '8')
        self.assertEqual(calendar1[1]['minutes'], '15')
        self.assertEqual(calendar1[2]['hour'], '8')
        self.assertEqual(calendar1[2]['minutes'], '30')
        self.assertEqual(calendar1[3]['hour'], '8')
        self.assertEqual(calendar1[3]['minutes'], '45')
        self.assertEqual(calendar1[4]['hour'], '9')
        self.assertEqual(calendar1[4]['minutes'], '00')
        self.assertEqual(calendar1[39]['hour'], '5')
        self.assertEqual(calendar1[39]['mil_hour'], '17')
        self.assertEqual(calendar1[39]['minutes'], '45')

    def test_get_raw_calendar2(self):
        settings.OPEN_TIME = "7:30"
        settings.CLOSE_TIME = "18:30"
        calendar1 = self.room1.get_raw_calendar()
        self.assertEqual(len(calendar1), 44)
        self.assertEqual(calendar1[0]['hour'], '7')
        self.assertEqual(calendar1[0]['mil_hour'], '7')
        self.assertEqual(calendar1[0]['minutes'], '30')
        self.assertEqual(calendar1[43]['hour'], '6')
        self.assertEqual(calendar1[43]['mil_hour'], '18')
        self.assertEqual(calendar1[43]['minutes'], '15')

    def test_get_calendar(self):
        calendar = self.room1.get_calendar()
        reserved_count = 0
        for block in calendar:
            if 'reserved' in block and block['reserved']:
                reserved_count = reserved_count + 1
        self.assertEqual(reserved_count, 20)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
