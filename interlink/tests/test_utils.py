
import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase
from django.core import management
from django.test.client import Client
from django.contrib.auth.models import User

def create_user(username, first_name, last_name, password='1234', email=None, is_staff=False, is_superuser=False):
   """Returns a tuple: (user, client)"""
   if email == None: email = '%s@nadine-test-yo.com' % (username)
   user = User.objects.create(username=username, first_name=first_name, last_name=last_name, email=email, is_staff=is_staff, is_superuser=is_superuser)
   user.set_password(password)
   user.save()
   client = Client()
   client.login(username=username, password=password)
   return (user, client)
