Events
======

For many coworking spaces, the ability to host and track events is very important. In Nadine, we have made it so that you can display a styled Google calendar or a built-in calendar using the PostgreSQL saved events.

Google Calendar Setup
---------------------

If you would like to use a Google Calendar then you must first create a Google calendar attached to a Google email account. It is with that account that you can add and edit events. Once that is done, you can proceed with connecting Nadine to this calendar then you just need to make a couple of additions to the local_settings.

To use a Google Calendar in the place of a local calendar, you will need to acquire a Google API key and the Google Calendar ID for previously created calendar. In **nadine/local_settings**, set each appropriately as GOOGLE_API_KEY and GOOGLE_CALENDAR_ID.

This calendar is only set to be viewable by members but not editable from the Members application. Members can click on events on the calendar and they will be redirected to the Google page including event details. Additionally, this calendar will not display member room bookings made within the application.

Built-In Calendar
-----------------

To use Nadine's built-in calendar, it is important to make sure that you do not have a GOOGLE_CALENDAR_ID in local_settings or comment it out if you do. There is only one optional setting in local_settings and that is to set colors for different rooms/spaces in the calendar. If interested in doing this, set it like the example below, with the room name and then color.

``CALENDAR_DICT = {'Pike': 'RGBA(249, 195, 50, 1)', 'Pine': 'RGBA(249, 195, 50, 1)'}``

The built-in calendar allows members and staff to add public events to the calendar. These are events that do not require an exclusive room booking and are along the lines of a Member Lunch, Lunch & Learn, Open House, etc. Members can click on the individual events to see time and host information. Additionally, members can add events to the calendar from clicking right on the date. These are only public events and not for a specific meeting room.

Room/Event Booking
------------------

If you opt to have room/event booking then you have a few items to set up. In local_settings set the hours when the space opens and closes. See example:

::

  OPEN_TIME = '8:00'
  CLOSE_TIME = '18:00'


In the Staff Application you can add rooms which members can book under settings/edit_rooms. The option of 'Members Only' means that a room is free for members to use and not bookable by general public. Once rooms are created, you can edit the CALENDAR_DICT with the room name.

If members can receive discounts on rooms then set MEMBER_DISCOUNT with a decimal amount. This will be applied for any room not set as 'Members Only'.

Members can have subscriptions for a certain number of room booking hours. Once they exceed an allowance then they will be charged the default hourly rate for the rooms.
