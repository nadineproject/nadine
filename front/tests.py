from datetime import datetime, timedelta, date
import traceback

from django.test import TestCase
from django.core import management
from django.contrib.auth.models import User

import settings
from staff.models import Bill, Transaction, Member, MonthlyLog, DailyLog, Onboard_Task, Onboard_Task_Completed, ExitTask, ExitTaskCompleted, Neighborhood
import staff.billing as billing

class FrontTestCase(TestCase):

   def setUp(self):
      pass
   
   def test_reminder(self):
      #TODO write scheduler tests
      #TODO write email tests
      #TODO write password reset tests
      print 'TODO: Write front tests'
   