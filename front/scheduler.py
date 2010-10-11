#!/usr/bin/python
"""
A task scheduling script which schedules tasks defined in settings.SCHEDULED_TASKS.
"""
import time
import threading
import readline
import traceback
import datetime
import cmd
import logging

class Task(threading.Thread):
   def __init__(self, action, loopdelay, initdelay):
      """The action is a function which will be called in a new thread every loopdelay microseconds, starting after initdelay microseconds"""
      self._action = action
      self._loopdelay = loopdelay
      self._initdelay = initdelay
      self._running = 1
      self.last_alert_datetime = None
      threading.Thread.__init__(self)

   def run(self):
      """There's no need to override this.  Pass your action in as a function to the __init__."""
      if self._initdelay: time.sleep(self._initdelay)
      self._runtime = time.time()
      while self._running:
         start = time.time()
         self._action()
         self._runtime += self._loopdelay
         time.sleep(max(0, self._runtime - start))

   def stop(self): self._running = 0

class Scheduler:
   """The class which manages the starting and stopping of tasks."""
   def __init__(self):
      self._tasks = []

   def __repr__(self): return '\n'.join(['%s' % task for task in self._tasks])

   def add_task(self, task): self._tasks.append(task)

   def start_all_tasks(self):
      print 'Starting scheduler'
      for task in self._tasks:
         print 'Starting task', task
         task.start()
      print 'All tasks started'

   def stop_all_tasks(self):
      for task in self._tasks:
         print 'Stopping task', task
         task.stop()
         task.join()
      print 'Stopped'

if __name__ == '__main__':
   import sys
   from django.core.management import setup_environ
   import settings

   setup_environ(settings)
   logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filename='/tmp/coworking-scheduler.txt', filemode = 'w')

   s = Scheduler()
   for task in settings.SCHEDULED_TASKS: s.add_task(task)
   s.start_all_tasks()

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
